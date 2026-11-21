"""
Homes – citizen house, cottage, apartment, quadplex and the player house (decoration).

HOUSE (family house; workshop corner from L2)
  Hearthwood  Tudor family house: brick ground storey, timber-framed plaster upper storey, steep tiled gable, outside
              brick chimney with inglenook. L2 workshop lean-to, L3 gabled porch + fenced front garden, L4 jettied
              front, L5 garden annex with the fifth bedroom.
  Cascadia    Log cabin: horizontal spruce logs on river-rock footing, deep full-width porch, stone chimney stack.
              L2 woodshed workshop lean-to, L3 sleeping loft, L4 back bedroom lean-to, L5 side deck.
  Neoterra    Modern villa: open-plan glass ground floor, cantilevered bedroom box above, flat roofs. L2 garage
              workshop, L3+ upper bedrooms, L5 roof terrace.
COTTAGE
  Hearthwood  Cotswold stone cottage (honey sandstone, deepslate-tile roof, dormers, cottage garden).
  Cascadia    A-frame cabin with a glazed gable and a deck; bunk lean-to later.
  Neoterra    Garden pavilion: low birch-and-glass box with a green roof; second pavilion joined by a glass link.
APARTMENT (one flat per citizen)
  Hearthwood  Victorian brick mansion block, two flats per floor around a central stair hall, dormered attic.
  Cascadia    Timber boarding house with a two-storey street gallery and outside stair.
  Neoterra    Mid-rise tower, one flat per storey with balconies, stair core, roof terrace.
QUADPLEX
  Hearthwood  Terrace of four Tudor town cottages, grown one house per level, chimneys on every party wall.
  Cascadia    Square two-storey fourplex: two flats down, two up off a covered gallery with an outside stair.
  Neoterra    Staggered modern townhouses (duplexes) with roof terraces.
PLAYER HOUSE
  Hearthwood  Manor house with a tithe-barn storehouse, smithy yard and a library.
  Cascadia    Homestead lodge with a big storage barn and workshop porch.
  Neoterra    Glass villa with a storage hall, workshop studio and library gallery.
"""
from hm import Design, design, AIR, D4
from blueprint import parse_state, format_state

OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}
CW = {"north": "east", "east": "south", "south": "west", "west": "north"}


# ============================================================================================ small block helpers
def stair(b, facing, half="bottom", shape="straight"):
    return f"{b}_stairs[facing={facing},half={half},shape={shape},waterlogged=false]" if not b.endswith("stairs") \
        else f"{b}[facing={facing},half={half},shape={shape},waterlogged=false]"


def slab(b, t="bottom"):
    b = b if b.endswith("slab") else b + "_slab"
    return f"{b}[type={t},waterlogged=false]"


def trap(wood, facing, half="top", open_=False):
    return f"{wood}_trapdoor[facing={facing},half={half},open={'true' if open_ else 'false'},powered=false," \
           f"waterlogged=false]"


def fence(wood):
    return f"{wood}_fence[east=false,north=false,south=false,waterlogged=false,west=false]"


def gate(wood, facing):
    return f"{wood}_fence_gate[facing={facing},in_wall=false,open=false,powered=false]"


def log(b, axis):
    return f"{b}[axis={axis}]"


def lantern(hanging=True, soul=False):
    return f"{'soul_' if soul else ''}lantern[hanging={'true' if hanging else 'false'},waterlogged=false]"


def cells(x1, z1, x2, z2):
    for z in range(min(z1, z2), max(z1, z2) + 1):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            yield x, z


def run(x, z, direction, n):
    dx, dz = D4[direction]
    return [(x + dx * i, z + dz * i) for i in range(n)]


def fit(d, items):
    """Place hand-picked pieces: items = [(x, y, z, block)] at absolute coordinates."""
    for x, y, z, b in items:
        d.set(x, y, z, b)


def BRL(f="up"):
    return f"barrel[facing={f},open=false]"


def CHEST(f):
    return f"chest[facing={f},type=single,waterlogged=false]"


def GRIND(f):
    return f"grindstone[face=floor,facing={f}]"


HAYX, HAYZ, HAYY = "hay_block[axis=x]", "hay_block[axis=z]", "hay_block[axis=y]"
CAUL = "water_cauldron[level=3]"
POT = "decorated_pot[cracked=false,facing=north,waterlogged=false]"
LANT = "lantern[hanging=true,waterlogged=false]"
LANTF = "lantern[hanging=false,waterlogged=false]"
CHAIN = "chain[axis=y,waterlogged=false]"


# ============================================================================================ circulation
def flight(d, x, z, y, n, direction, block, support=None):
    """Straight flight of n stairs starting at (x,z) on walking level y, climbing toward `direction`.
    Clears 3 blocks above every step. Returns the landing cell (x, z, walking y) after the last step."""
    dx, dz = D4[direction]
    for i in range(n):
        cx, cz, h = x + dx * i, z + dz * i, y + i
        d.set(cx, h, cz, stair(block, direction))
        for k in (1, 2, 3):
            if d.bp.inside(cx, h + k, cz):
                d.set(cx, h + k, cz, AIR)
        if support:
            for yy in range(y, h):
                d.set(cx, yy, cz, support)
    return x + dx * n, z + dz * n, y + n



def partition(d, x1, z1, x2, z2, y1, y2, block, doors=(), wood=None):
    """Interior wall with doors [(x, z, facing)]."""
    d.fill(x1, y1, z1, x2, y2, z2, block)
    for x, z, f in doors:
        d.door(x, y1, z, f, wood)
        for yy in range(y1 + 2, y2 + 1):
            d.set(x, yy, z, block)


# ============================================================================================ furniture
def kitchen(d, seq, y, facing, wood=None, top=None, shelf=True):
    """A run of kitchen units listed cell by cell: seq = [(x, z, kind)], kind in furnace / smoker /
    crafting_table / barrel / sink / counter / cauldron; `facing` = the side the fronts face."""
    wood = wood or d.P["wood"]
    for x, z, k in seq:
        if k in ("furnace", "smoker", "crafting_table", "barrel", "blast_furnace"):
            d.item(x, y, z, k, facing if k != "crafting_table" else None)
        elif k == "sink":
            d.set(x, y, z, "water_cauldron[level=3]")
        elif k == "cauldron":
            d.item(x, y, z, "water_cauldron[level=3]")
        else:
            d.set(x, y, z, top or stair(wood, OPP[facing], "top"))


def nightstand(d, x, y, z, wood=None, light="candle"):
    wood = wood or d.P["wood"]
    d.set(x, y, z, slab(wood, "top"))
    if light == "candle":
        d.candle(x, y + 1, z, 1)
    elif light == "lantern":
        d.set(x, y + 1, z, lantern(False))
    elif light:
        d.set(x, y + 1, z, light)


def bedset(d, x, y, z, facing, stands=("l", "r"), color=None, wood=None, light="candle"):
    """Bed with its head at (x,z) against a wall (`facing` = toward that wall) and nightstands beside the head."""
    d.bed(x, y, z, facing, color)
    lx, lz = D4[CW[facing]]
    for s in stands:
        sx, sz = (x + lx, z + lz) if s == "r" else (x - lx, z - lz)
        if d.air(sx, y, sz):
            nightstand(d, sx, y, sz, wood, light)


def sofa(d, x, z, y, n, along, back, wood=None, arms=True, sit=True):
    """n chairs in a row starting at (x,z) along `along` (a direction), backs to `back`."""
    pts = run(x, z, along, n)
    for cx, cz in pts:
        d.chair(cx, y, cz, back, wood, sit)
    if arms:
        wood = wood or d.P["wood"]
        for (cx, cz), side in ((pts[0], OPP[along]), (pts[-1], along)):
            ox, oz = D4[side]
            if d.air(cx + ox, y, cz + oz):
                d.set(cx + ox, y, cz + oz, trap(wood, side, "bottom", True))
    return n


def wardrobe(d, x, y, z, facing, wood=None):
    """Two-high cupboard: a barrel-free chest with a plank top cabinet."""
    wood = wood or d.P["wood"]
    d.set(x, y, z, f"chest[facing={facing},type=single,waterlogged=false]")
    d.set(x, y + 1, z, f"{wood}_planks" if not wood.startswith("smooth") else wood)



def rugc(d, x1, z1, x2, z2, y, color):
    for x, z in cells(x1, z1, x2, z2):
        if d.air(x, y, z):
            d.set(x, y, z, f"{color}_carpet")


def garden(d, x1, z1, x2, z2, y, wood, gates=(), plants=(), border=True, **_):
    """Fenced lawn x1..x2/z1..z2 with gates [(x, z, facing)] and hand-placed plants [(x, z, block)]."""
    for x, z in cells(x1, z1, x2, z2):
        d.set(x, y - 1, z, "grass_block[snowy=false]")
        d.set(x, y, z, AIR)
    gs = {(gx, gz) for gx, gz, _f in gates}
    if border:
        for x, z in cells(x1, z1, x2, z2):
            if (x in (x1, x2) or z in (z1, z2)) and (x, z) not in gs:
                d.set(x, y, z, fence(wood))
    for gx, gz, f in gates:
        d.set(gx, y, gz, gate(wood, f))
    for x, z, b in plants:
        d.set(x, y, z, b)
        if b.endswith("[half=lower]"):
            d.set(x, y + 1, z, b.replace("lower", "upper"))


def path(d, pts, y, block):
    for x, z in pts:
        d.set(x, y, z, block)


def clear_above_path(d, pts, y):
    for x, z in pts:
        for k in (1, 2):
            n = d.get(x, y + k, z)
            if n != AIR and ("flower" in n or "poppy" in n or "daisy" in n or "allium" in n or "bluet" in n
                             or "dandelion" in n):
                d.set(x, y + k, z, AIR)


# ============================================================================================ pack shells
# ---- Hearthwood
def hw_walls(d, x1, z1, x2, z2, y1, y2, fill="calcite", post="dark_oak_log", step=3, base=None, brace=False):
    """Timber-framed walls: plaster infill, posts at corners and every `step`, a beam on top (y2), optional
    base course. Interior is NOT cleared."""
    for y in range(y1, y2 + 1):
        for x, z in cells(x1, z1, x2, z2):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, y, z, fill)
    for x in range(x1, x2 + 1):
        for z in (z1, z2):
            if (x - x1) % step == 0 or x == x2:
                for y in range(y1, y2):
                    d.set(x, y, z, log(post, "y"))
            d.set(x, y2, z, log(post, "x"))
            if base:
                d.set(x, y1, z, base)
    for z in range(z1, z2 + 1):
        for x in (x1, x2):
            if (z - z1) % step == 0 or z == z2:
                for y in range(y1, y2):
                    d.set(x, y, z, log(post, "y"))
            d.set(x, y2, z, log(post, "z"))
            if base:
                d.set(x, y1, z, base)


def brick_walls(d, x1, z1, x2, z2, y1, y2, block="bricks", base="stone_bricks", quoin=None):
    for y in range(y1, y2 + 1):
        for x, z in cells(x1, z1, x2, z2):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, y, z, base if (y == y1 and base) else block)
    if quoin:
        for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
            for y in range(y1, y2 + 1):
                d.set(x, y, z, quoin if (y - y1) % 2 == 0 else block)


def hw_window(d, x, y, z, h=2, box_dir=None, glass="glass_pane"):
    for k in range(h):
        d.set(x, y + k, z, glass)
    if box_dir:
        ox, oz = D4[box_dir]
        if d.bp.inside(x + ox, y - 1, z + oz) and d.air(x + ox, y - 1, z + oz):
            d.set(x + ox, y - 1, z + oz, trap("dark_oak", box_dir, "top"))



def fireplace(d, wx, wz, y, inward, top, frame="bricks", stack=None, fire="campfire", width=3, stack_out=True):
    """Fireplace in an outside wall: fire recessed in the wall cell (wx,wz), jambs either side in the wall,
    mantel above, a 3-wide chimney breast outside the wall up to `top` (stack narrows to 1 above the eaves via the
    roof covering the sides – caller decides). `inward` = direction into the room."""
    stack = stack or frame
    sx, sz = D4[CW[inward]]
    ox, oz = D4[OPP[inward]]
    for k in range(-(width // 2), width // 2 + 1):
        cx, cz = wx + sx * k, wz + sz * k
        if k == 0:
            d.set(cx, y, cz, f"{fire}[facing={inward},lit=true,signal_fire=false,waterlogged=false]")
        else:
            d.set(cx, y, cz, frame)
        d.set(cx, y + 1, cz, frame)
    ix, iz = wx - ox, wz - oz
    # mantel: a shelf over the hearth front with candles and a pot
    for k, item in ((-1, "candle[candles=2,lit=false,waterlogged=false]"), (0, None),
                    (1, "decorated_pot[cracked=false,facing=north,waterlogged=false]")):
        cx, cz = ix + sx * k, iz + sz * k
        if d.bp.inside(cx, y + 2, cz) and d.air(cx, y + 2, cz) and d.air(cx, y + 3, cz):
            d.set(cx, y + 2, cz, slab("dark_oak" if fire == "campfire" else "smooth_quartz", "top"))
            if item:
                d.set(cx, y + 3, cz, item)
    if stack_out:
        for k in range(-(width // 2), width // 2 + 1):
            cx, cz = wx + ox + sx * k, wz + oz + sz * k
            for yy in range(y - 1, y + 3):
                d.set(cx, yy, cz, stack)
        for yy in range(y + 3, top):
            d.set(wx + ox, yy, wz + oz, stack)
        # sloped shoulders
        for k in (-1, 1):
            cx, cz = wx + ox + sx * k, wz + oz + sz * k
            f = {(-1): OPP[CW[inward]], 1: CW[inward]}[k]
            if stack in ("bricks", "cobblestone", "stone_bricks", "mossy_cobblestone", "polished_blackstone_bricks",
                         "deepslate_bricks"):
                sb = {"bricks": "brick", "cobblestone": "cobblestone", "stone_bricks": "stone_brick",
                      "mossy_cobblestone": "mossy_cobblestone", "polished_blackstone_bricks":
                          "polished_blackstone_brick", "deepslate_bricks": "deepslate_brick"}[stack]
                d.set(cx, y + 3, cz, stair(sb, OPP[f]))
        d.set(wx + ox, top, wz + oz, stack)
        cap = {"bricks": "brick_wall", "cobblestone": "cobblestone_wall", "mossy_cobblestone": "mossy_cobblestone_wall",
               "stone_bricks": "stone_brick_wall", "polished_blackstone_bricks": "polished_blackstone_brick_wall",
               "deepslate_bricks": "deepslate_brick_wall"}.get(stack)
        if cap and d.bp.inside(wx + ox, top + 1, wz + oz):
            d.set(wx + ox, top + 1, wz + oz, f"{cap}[east=none,north=none,south=none,up=true,waterlogged=false,"
                                             f"west=none]")


def shed_roof(d, x1, z1, x2, z2, y, down, block, under=None, overhang=1):
    """Lean-to roof over x1..x2/z1..z2 falling toward `down`; the low edge sits at y on the `down` wall."""
    up = OPP[down]
    dx, dz = D4[down]
    if down in ("east", "west"):
        lo_edge = x2 if down == "east" else x1
        cols = range(x1, x2 + 1)
        span = [(c, abs(lo_edge - c)) for c in cols]
        for c, k in span + [(lo_edge + dx * overhang, -overhang)]:
            for z in range(z1 - overhang, z2 + overhang + 1):
                if d.bp.inside(c, y + k, z):
                    d.set(c, y + k, z, stair(block, up))
    else:
        lo_edge = z2 if down == "south" else z1
        rows = range(z1, z2 + 1)
        span = [(r, abs(lo_edge - r)) for r in rows]
        for r, k in span + [(lo_edge + dz * overhang, -overhang)]:
            for x in range(x1 - overhang, x2 + overhang + 1):
                if d.bp.inside(x, y + k, r):
                    d.set(x, y + k, r, stair(block, up))



def log_walls(d, x1, z1, x2, z2, y1, y2, logb="spruce_log", post="stripped_spruce_log", footing=True, plinth=True):
    def log(b, a):
        return f"{b}[axis={a}]" if ("log" in b or b.endswith("_wood")) else b
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            d.set(x, y, z1, log(logb, "x"))
            d.set(x, y, z2, log(logb, "x"))
        for z in range(z1, z2 + 1):
            d.set(x1, y, z, log(logb, "z"))
            d.set(x2, y, z, log(logb, "z"))
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        for y in range(y1, y2 + 1):
            d.set(x, y, z, log(post, "y"))
    if footing:
        for x, z in cells(x1, z1, x2, z2):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, y1 - 1, z, "mossy_cobblestone" if (x * 7 + z * 3) % 5 == 0 else "cobblestone")
                if plinth:
                    d.set(x, y1, z, "mossy_cobblestone" if (x * 5 + z * 3) % 4 == 0 else "cobblestone")


def ca_window(d, x, y, z, out, h=2, shutters=True, w=1):
    """Window in a log wall, `out` = outward direction; spruce shutters (open trapdoors) either side outside."""
    sx, sz = D4[CW[out]]
    for i in range(w):
        for k in range(h):
            d.set(x + sx * i, y + k, z + sz * i, "glass_pane")
    ox, oz = D4[out]
    if shutters:
        for (cx, cz), side in (((x - sx + ox, z - sz + oz), OPP[CW[out]]),
                               ((x + sx * w + ox, z + sz * w + oz), CW[out])):
            for k in range(h):
                if d.bp.inside(cx, y + k, cz) and d.air(cx, y + k, cz):
                    d.set(cx, y + k, cz, trap("dark_oak", side, "bottom", True))


# ---- Neoterra
def nt_box(d, x1, z1, x2, z2, y1, y2, wall="white_concrete", corner="light_gray_concrete"):
    for y in range(y1, y2 + 1):
        for x, z in cells(x1, z1, x2, z2):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, y, z, corner if (x in (x1, x2) and z in (z1, z2)) else wall)




def planter(d, x1, z1, x2, z2, y, plants=("azalea", "flowering_azalea", "fern")):
    for i, (x, z) in enumerate(cells(x1, z1, x2, z2)):
        d.set(x, y, z, "moss_block" if i % 3 else "grass_block[snowy=false]")
        p = plants[i % len(plants)]
        if d.air(x, y + 1, z):
            d.set(x, y + 1, z, p if p != "fern" else "fern")


# ============================================================================================ HOUSE
def house_hw(rel, L, v=0):
    d = Design("Hearthwood", rel, (24, 26, 25), paving="grass_block[snowy=false]")
    W = "dark_oak"
    x1, x2, z1, z2 = 4, 14, 7, 16
    y0, deck, yu, top = 2, 6, 7, 9
    jet = L >= 4
    uz1 = z1 - 1 if jet else z1
    # ground storey: brick on a stone plinth; upper: framed plaster
    brick_walls(d, x1, z1, x2, z2, y0, deck - 1, "bricks", "stone_bricks")
    d.fill(x1 + 1, y0 - 1, z1 + 1, x2 - 1, y0 - 1, z2 - 1, "spruce_planks")
    d.clear(x1 + 1, y0, z1 + 1, x2 - 1, deck - 1, z2 - 1)
    d.fill(x1, deck, uz1, x2, deck, z2, "dark_oak_planks")
    hw_walls(d, x1, uz1, x2, z2, yu, top, "calcite", "dark_oak_log", step=2)
    d.clear(x1 + 1, yu, uz1 + 1, x2 - 1, top, z2 - 1)
    if jet:
        for x in range(x1, x2 + 1, 2):
            d.set(x, deck - 1, uz1, stair(W, "south", "top"))
    # roof
    ridge = d.gable(x1, uz1, x2, z2, top + 1, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite")
    zc = (uz1 + z2) // 2
    for x in (x1, x2):
        for yy in range(top + 1, ridge):
            if d.get(x, yy, zc) == "minecraft:calcite":
                d.set(x, yy, zc, log("dark_oak_log", "y"))
    # openings
    dx_ = 9
    d.door(dx_, y0, z1, "south", W)
    d.set(dx_, y0 + 2, z1, "stone_bricks")
    for x in (6, 7, 11, 12):
        hw_window(d, x, 3, z1, 2)
    for x in (6, 12):
        hw_window(d, x, 3, z2, 2)
    for z in (9, 13):
        hw_window(d, x2, 3, z, 2)
    for x in (5, 7, 11, 13):
        hw_window(d, x, yu + 1, uz1, 1, "north")
    for x in (7, 11):
        hw_window(d, x, yu + 1, z2, 1, "south")
    for z in (zc - 1, zc + 2):
        for x in (x1, x2):
            if not (L >= 2 and x == x2):
                d.set(x, yu + 1, z, "glass_pane")
    # ---- ground floor
    fireplace(d, x1, 11, y0, "east", ridge + 2, "bricks")
    d.hut(5, y0, 8)
    if v == 0:      # settle facing the inglenook, dining table for four by the window
        rugc(d, 5, 10, 6, 12, y0, "red")
        sofa(d, 7, 10, y0, 3, "south", "east", "dark_oak")
        d.set(5, y0, 9, "potted_red_tulip")
        d.dining(10, y0, 10, 2, "z", "dark_oak", ("e", "w"))
    else:           # dower house: two wing chairs at the fire, round table, dresser with plates
        rugc(d, 5, 10, 6, 12, y0, "green")
        fit(d, [(6, y0, 10, stair("dark_oak", "east")), (6, y0, 12, stair("dark_oak", "east")),
                (5, y0, 9, "potted_azure_bluet"), (8, y0, 8, CHEST("south")), (8, y0 + 1, 8, POT)])
        d.dining(9, y0, 11, 1, "x", "dark_oak", ("n", "s", "e", "w"), sit=False)
    d.lamp(10, deck - 1, 10)
    d.lamp(6, deck - 1, 11)
    # kitchen along the back wall (east half) and east wall
    kitchen(d, [(13, z2 - 1, "furnace"), (12, z2 - 1, "sink"), (11, z2 - 1, "smoker")], y0, "north", "dark_oak")
    kitchen(d, [(13, 13, "crafting_table"), (13, 12, "barrel")], y0, "west", "dark_oak")
    d.item(13, y0, 14, "barrel", "up")
    d.set(13, y0 + 1, 14, "potted_fern")
    # stairs along the back wall, west half, rising east
    sx0 = 6
    lx, lz, ly = flight(d, sx0, z2 - 1, y0, 5, "east", "dark_oak", support="dark_oak_planks")
    for x in range(sx0 + 1, sx0 + 4):
        d.set(x, yu, z2 - 2, fence(W))
    d.set(sx0, yu, z2 - 2, fence(W))
    d.set(5, y0, z2 - 1, AIR)
    # ---- upper floor: two bedrooms off a landing corridor
    d.fill(x1 + 1, yu, 12, x2 - 1, top, 12, "calcite")
    for x in range(x1 + 2, x2, 2):
        for y in range(yu, top):
            d.set(x, y, 12, log("stripped_dark_oak_log", "y"))
    d.fill(9, yu, uz1 + 1, 9, top, 11, "calcite")
    d.door(7, yu, 12, "north", W)
    d.door(11, yu, 12, "north", W)
    for x in (7, 11):
        d.set(x, top, 12, "calcite")
    # room A (west): master
    bz = uz1 + 1
    bedset(d, 6, yu, bz, "north", ("l",), "red", W)
    if L >= 2:
        bedset(d, 7, yu, bz, "north", ("r",), "red", W)
    wardrobe(d, 5, yu, 11, "east", W)
    rugc(d, 6, bz + 2, 8, 10, yu, "white")
    d.lamp(7, top, 9)
    # room B (east)
    if L >= 3:
        bedset(d, 12, yu, bz, "north", ("r",), "blue", W)
    if L >= 4:
        bedset(d, 11, yu, bz, "north", ("l",), "light_blue", W)
    if L < 3:
        d.set(12, yu, bz, "loom[facing=south]")
        d.chair(12, yu, bz + 1, "south", W, sit=False)
    wardrobe(d, 13, yu, 11, "west", W)
    d.lamp(11, top, 9)
    rugc(d, 10, 9, 12, 10, yu, "light_blue")
    # landing
    d.lamp(12, top, 14)
    d.set(13, yu, 15, "potted_fern")
    # ---- L2 workshop lean-to (east)
    if L >= 2:
        wx1, wx2, wz1, wz2 = x2, 19, 10, 16
        brick_walls(d, wx1, wz1, wx2, wz2, y0, 4, "bricks", "stone_bricks")
        d.clear(wx1 + 1, y0, wz1 + 1, wx2 - 1, 4, wz2 - 1)
        d.fill(wx1 + 1, y0 - 1, wz1 + 1, wx2 - 1, y0 - 1, wz2 - 1, "stone_bricks")
        shed_roof(d, wx1 + 1, wz1, wx2, wz2, 5, "east", "deepslate_tile")
        # close the triangles on the lean-to's north / south walls
        for x in range(wx1 + 1, wx2):
            for y in range(5, 5 + (wx2 - x)):
                for z in (wz1, wz2):
                    d.set(x, y, z, "bricks")
        d.double_door(16, y0, wz1, "x", "south", "spruce")
        d.set(16, 4, wz1, log("dark_oak_log", "x"))
        d.set(17, 4, wz1, log("dark_oak_log", "x"))
        hw_window(d, wx2, 3, 13, 1)
        d.item(15, y0, wz2 - 1, "smithing_table")
        d.item(16, y0, wz2 - 1, "anvil", "east")
        d.item(17, y0, wz2 - 1, "grindstone", "east")
        d.item(18, y0, wz2 - 1, "crafting_table")
        d.item(18, y0, wz2 - 2, "barrel", "west")
        d.set(18, y0, wz2 - 3, "barrel[facing=up,open=false]")
        d.set(15, y0, wz1 + 1, "chest[facing=east,type=single,waterlogged=false]")
        d.lamp(16, 4, 13)
    # ---- L3 porch + garden
    gz2 = z1 - 1
    if L >= 3:
        gz2 = z1 - 2 - (1 if jet else 0)
        garden(d, 2, 1, 21, gz2, y0, "spruce", gates=((9, 1, "north"), (9, gz2, "north")),
               plants=((3, 2, "rose_bush[half=lower]"), (4, 2, "poppy"), (6, 2, "oxeye_daisy"), (7, 2, "allium"),
                       (11, 2, "cornflower"), (15, 2, "azure_bluet"), (16, 2, "red_tulip"),
                       (19, 2, "lilac[half=lower]"), (20, 2, "dandelion")))
        path(d, [(9, z) for z in range(0, z1)], y0 - 1, "gravel")
        clear_above_path(d, [(9, z) for z in range(0, z1)], y0 - 1)
        for z in range(1, z1):
            if d.get(9, y0, z) not in (AIR,) and "gate" not in d.get(9, y0, z):
                d.set(9, y0, z, AIR)
        # garden bench (seats)
        d.chair(5, y0, 3, "west", "spruce")
        d.chair(5, y0, 4, "west", "spruce")
        if L >= 4:
            d.chair(13, y0, 3, "east", "spruce")
            d.chair(13, y0, 4, "east", "spruce")
            d.table(12, y0, 3, "spruce")
        d.set(17, y0, 3, "flowering_azalea")
        # porch hood over the door on brackets
        for x in (8, 9, 10):
            d.set(x, y0 + 3, z1 - 1, slab("deepslate_tile"))
        d.set(8, y0 + 2, z1 - 1, stair(W, "south", "top"))
        d.set(10, y0 + 2, z1 - 1, stair(W, "south", "top"))
    else:
        path(d, [(9, z) for z in range(0, z1)], y0 - 1, "gravel")
    d.lamp(10, y0 + 1, z1 - 1, "lantern", hanging=False) if L < 3 else None
    # ---- L5 garden annex (fifth bedroom) + jukebox + ender chest
    if L >= 5:
        ax1, ax2, az1, az2 = 4, 10, z2, 22
        hw_walls(d, ax1, az1, ax2, az2, y0, 4, "calcite", "dark_oak_log", 3, "stone_bricks")
        d.clear(ax1 + 1, y0, az1 + 1, ax2 - 1, 4, az2 - 1)
        d.fill(ax1 + 1, y0 - 1, az1 + 1, ax2 - 1, y0 - 1, az2 - 1, "oak_planks")
        d.gable(ax1, az1 + 2, ax2, az2, 5, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite")
        d.door(ax2, y0, 20, "west", W)
        hw_window(d, ax1, 3, 19, 2)
        hw_window(d, 7, 3, az2, 2)
        bedset(d, 6, y0, az2 - 1, "south", ("l",), "green", W)
        d.item(8, y0, az2 - 1, "ender_chest", "north")
        d.chair(8, y0, az1 + 2, "north", W, sit=False)
        d.set(5, y0, az1 + 1, "bookshelf")
        d.lamp(7, 4, 19)
        d.item(5, y0, 13, "jukebox")
        d.set(ax2 + 1, y0 - 1, 20, "gravel")
        for x in range(ax2 + 1, 15):
            d.set(x, y0 - 1, 19, "gravel")
    return d


def house_ca(rel, L):
    d = Design("Cascadia", rel, (27, 26, 25), paving="grass_block[snowy=false]")
    W, LOG = "spruce", "spruce_log"
    x1, x2, z1, z2 = 5, 17, 8, 16
    y0 = 2
    log_walls(d, x1, z1, x2, z2, y0, 6, "stripped_spruce_log", LOG)
    d.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, z2 - 1, "spruce_planks")
    d.clear(x1 + 1, y0, z1 + 1, x2 - 1, 6, z2 - 1)
    # dark trim band under the eaves
    for x in range(x1, x2 + 1):
        for z in (z1, z2):
            d.set(x, 6, z, log("spruce_log", "x"))
    ridge = d.gable(x1, z1, x2, z2, 7, "x", "dark_oak_stairs", "dark_oak_slab", log("stripped_spruce_log", "z"))
    mid = (z1 + z2) // 2
    for x in (x1, x2):                                    # gable vent window
        d.set(x, ridge - 2, mid, "glass_pane")
    # porch
    pz = z1 - 4
    for x in range(x1, x2 + 1):
        for z in range(pz, z1):
            d.set(x, 1, z, "spruce_planks")
    for x in (x1, 9, 13, x2):
        for y in range(y0, 5):
            d.set(x, y, pz, log(LOG, "y"))
        d.set(x, 1, pz, "cobblestone")
    for x in range(x1 - 1, x2 + 2):
        d.set(x, 5, pz - 1, stair("dark_oak", "south"))
        d.set(x, 5, pz, stair("dark_oak", "south"))
        d.set(x, 5, pz + 1, slab("dark_oak", "top"))
        d.set(x, 6, pz + 2, stair("dark_oak", "south"))
        d.set(x, 6, pz + 3, stair("dark_oak", "south"))
    for x in range(x1 + 1, x2):
        if x not in (9, 13, 11):
            d.set(x, y0, pz, fence(W))
    for x in (10, 11, 12):
        d.set(x, 1, pz - 1, stair("spruce", "south"))
    for z in range(0, pz - 1):
        for x in (10, 11, 12):
            d.set(x, 1, z, "coarse_dirt" if (x + z) % 3 else "gravel")
    d.lamp(11, 4, pz + 1)
    d.chair(7, y0, z1 - 1, "south", W, sit=L >= 4)
    d.chair(8, y0, z1 - 1, "south", W, sit=L >= 4)
    d.set(6, y0, z1 - 1, "barrel[facing=up,open=false]")
    d.set(6, y0 + 1, z1 - 1, "potted_fern")
    for x in (14, 15, 16):                                # firewood stack
        d.set(x, y0, z1 - 1, log("spruce_log", "x"))
    d.set(15, y0 + 1, z1 - 1, log("spruce_log", "x"))
    # openings
    d.door(11, y0, z1, "south", W)
    for x in (7, 15):
        ca_window(d, x, 3, z1, "north", 2, w=2 if x == 7 else 1)
    ca_window(d, 14, 3, z2, "south", 2)
    ca_window(d, 7, 3, z2, "south", 2)
    if L < 2:
        ca_window(d, x2, 3, 12, "east", 2)
    # ---- one big room: hearth, sitting, table, kitchen, bed corner
    fireplace(d, x1, 12, y0, "east", ridge + 2, "cobblestone", "mossy_cobblestone")
    for y in range(y0 + 2, ridge + 2):
        d.set(x1 - 1, y, 12, "cobblestone" if y % 3 else "mossy_cobblestone")
    rugc(d, 6, 11, 7, 13, y0, "brown")
    sofa(d, 8, 11, y0, 3, "south", "east", W)
    d.hut(6, y0, 9)
    d.dining(12, y0, 12, 2, "x", W, ("n", "s"))
    d.lamp(12, 5, 12)
    d.lamp(7, 5, 12)
    kitchen(d, [(11, 15, "barrel"), (12, 15, "furnace"), (13, 15, "sink"), (14, 15, "smoker"),
                (15, 15, "crafting_table"), (16, 15, "barrel")], y0, "north", W)
    # bed corner (double from L2)
    bedset(d, 16, y0, 10, "east", ("r",), "brown", W)
    if L >= 2:
        d.bed(16, y0, 9, "east", "brown")
    # ---- loft (L3+): deck over the east half, stair along x=10 rising north
    if L >= 3:
        d.fill(11, 6, z1 + 1, x2 - 1, 6, z2 - 1, "spruce_planks")
        d.fill(10, 6, 9, 10, 6, 10, "spruce_planks")
        flight(d, 10, 15, y0, 5, "north", W, support=None)
        bedset(d, 16, 7, 11, "east", ("r",), "green", W, light="lantern")
        if L >= 5:
            d.bed(16, 7, 13, "east", "lime")
        d.set(15, 7, 14, "chest[facing=north,type=single,waterlogged=false]")
        rugc(d, 12, 11, 14, 13, 7, "green")
        for x in range(11, 16):
            d.set(x, 7, 9, fence(W))
    # ---- L2 woodshed workshop lean-to
    if L >= 2:
        wx1, wx2, wz1, wz2 = x2, 22, z1 + 1, z2
        for z in range(wz1, wz2 + 1):
            for y in range(y0, 5):
                d.set(wx2, y, z, "spruce_planks")
        for x in range(wx1, wx2 + 1):
            for y in range(y0, 5):
                d.set(x, y, wz2, "spruce_planks")
        for x, z in ((wx2, wz1), (wx2, wz2)):
            for y in range(y0, 5):
                d.set(x, y, z, log(LOG, "y"))
        for x, z in cells(wx1 + 1, wz1, wx2 - 1, wz2 - 1):
            d.set(x, 1, z, "packed_mud")
        shed_roof(d, wx1 + 1, wz1, wx2, wz2, 5, "east", "spruce")
        for x in range(wx1 + 1, wx2):
            for y in range(5, 5 + (wx2 - x)):
                d.set(x, y, wz2, "spruce_planks")
        # open front with a log beam
        for x in range(wx1 + 1, wx2 + 1):
            d.set(x, 4, wz1, log("stripped_spruce_log", "x"))
            for y in range(5, 5 + (wx2 - x)):
                d.set(x, y, wz1, "spruce_planks")
        d.set(wx2, y0, wz1, log(LOG, "y")) 
        d.item(18, y0, wz2 - 1, "smithing_table")
        d.item(19, y0, wz2 - 1, "anvil", "east")
        d.item(20, y0, wz2 - 1, "grindstone", "east")
        d.item(21, y0, wz2 - 1, "crafting_table")
        d.item(21, y0, wz2 - 2, "barrel", "west")
        d.set(21, y0, wz2 - 3, log("spruce_log", "y"))
        d.lamp(19, 4, 12)
        for z in (11, 12):
            for y in (y0, y0 + 1):
                d.set(21, y, z, log("spruce_log", "x"))
    # ---- L4 back bedroom lean-to
    if L >= 4:
        bx1, bx2, bz1, bz2 = 5, 10, z2, 21
        log_walls(d, bx1, bz1, bx2, bz2, y0, 4, "stripped_spruce_log", LOG)
        d.clear(bx1 + 1, y0, bz1 + 1, bx2 - 1, 4, bz2 - 1)
        d.fill(bx1 + 1, 1, bz1 + 1, bx2 - 1, 1, bz2 - 1, "spruce_planks")
        shed_roof(d, bx1, bz1 + 1, bx2, bz2, 5, "south", "dark_oak")
        for z in range(bz1 + 1, bz2):
            for y in range(5, 5 + (bz2 - z)):
                for x in (bx1, bx2):
                    d.set(x, y, z, log("stripped_spruce_log", "z"))
        d.door(8, y0, z2, "south", W)
        bedset(d, 7, y0, bz2 - 1, "south", ("l",), "cyan", W)
        if L >= 5:
            d.item(9, y0, bz2 - 1, "ender_chest", "north")
        d.set(6, y0, bz1 + 1, "chest[facing=east,type=single,waterlogged=false]")
        ca_window(d, bx1, 3, 19, "west", 1)
        d.lamp(7, 4, 18)
    if L >= 5:
        d.item(6, y0, 14, "jukebox")
        # side deck with chairs
        for x, z in cells(0, 10, x1 - 2, 15):
            d.set(x, 1, z, "spruce_planks")
        for z in range(10, 16):
            d.set(0, y0, z, fence(W))
        d.chair(1, y0, 11, "north", W, sit=False)
        d.chair(1, y0, 14, "south", W, sit=False)
        d.table(1, y0, 12, W)
    return d


def house_nt(rel, L, v=0):
    d = Design("Neoterra", rel, (23, 26, 23), paving="smooth_stone")
    x1, x2, z1, z2 = 3, 15, 6, 15
    y0 = 2
    nt_box(d, x1, z1, x2, z2, y0, 5)
    d.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, z2 - 1, "polished_diorite")
    d.clear(x1 + 1, y0, z1 + 1, x2 - 1, 5, z2 - 1)
    up = L >= 3
    # glass street front with birch slat piers
    for x in range(x1 + 1, x2):
        if x in (7, 12):
            continue
        d.window(x, y0, z1, x, 4, z1)
    for x in (7, 12):
        for y in range(y0, 5):
            d.set(x, y, z1, log("stripped_birch_log", "y"))
    d.double_door(9, y0, z1, "x", "south", "birch")
    for z in (8, 11):
        d.window(x1, 3, z, x1, 4, z)
    for x in (5, 6):
        d.window(x, 3, z2, x, 4, z2)
    # roof / upper deck
    d.fill(x1, 6, z1, x2, 6, z2, "smooth_quartz")
    if not up:
        for x, z in cells(x1, z1, x2, z2):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, 7, z, "white_concrete")
                d.set(x, 8, z, slab("smooth_quartz"))
    for x in range(x1 - 1, x2 + 2):                       # canopy lip over the glass front
        d.set(x, 6, z1 - 1, slab("smooth_quartz", "top"))
    d.fill(x1, 5, z1, x2, 5, z1, "light_gray_concrete")
    # ---- ground floor: living (west), dining, kitchen (back), bedroom (east)
    fireplace(d, x1, 11, y0, "east", 9 if not up else 12, "polished_blackstone_bricks", "polished_blackstone_bricks",
              "soul_campfire", stack_out=True)
    d.hut(5, y0, 7)
    if v == 0:      # lounge: sofa facing the linear fire, dining table for four
        rugc(d, 4, 9, 5, 13, y0, "light_gray")
        sofa(d, 6, 10, y0, 3, "south", "east", "birch", arms=False)
        d.set(6, y0, 9, "birch_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]")
        d.set(4, y0, 7, "potted_bamboo")
        d.dining(9, y0, 10, 2, "x", "birch", ("n", "s"))
    elif v == 1:    # guest villa 1: reading lounge – two armchairs at the fire, round table, books
        rugc(d, 4, 10, 6, 12, y0, "orange")
        fit(d, [(6, y0, 10, stair("birch", "east")), (6, y0, 12, stair("birch", "east")),
                (8, y0, 9, slab("smooth_quartz", "top")), (8, y0 + 1, 9, "potted_azure_bluet"),
                (10, y0, 8, "bookshelf"), (10, y0 + 1, 8, "potted_fern"), (10, y0, 13, "potted_bamboo")])
        d.dining(8, y0, 11, 1, "x", "birch", ("n", "s", "e"), sit=False)
    elif v == 2:    # guest villa 2: long dinner table, sideboard and a plant by the window
        rugc(d, 5, 9, 9, 11, y0, "lime")
        d.dining(6, y0, 10, 3, "x", "birch", ("n", "s"), sit=False)
        fit(d, [(10, y0, 12, CHEST("west")), (10, y0 + 1, 12, POT), (4, y0, 9, "potted_bamboo")])
    else:           # guest villa 3: music room – sofa across the room, jukebox, rug
        sofa(d, 7, 12, y0, 3, "east", "south", "birch", arms=False, sit=False)
        rugc(d, 6, 9, 9, 10, y0, "magenta")
        fit(d, [(10, y0, 9, "note_block[instrument=harp,note=0,powered=false]"), (4, y0, 13, "potted_bamboo"),
                (10, y0, 12, slab("smooth_quartz", "top")), (10, y0 + 1, 12, "candle[candles=3,lit=false,waterlogged=false]")])
    for x, z in ((9, 10), (5, 11), (13, 9)):
        d.set(x, 5, z, "sea_lantern")
    # kitchen back wall west half
    kitchen(d, [(4, 14, "barrel"), (5, 14, "barrel"), (6, 14, "furnace"), (7, 14, "smoker"), (8, 14, "sink"),
                (9, 14, "crafting_table")], y0, "north", "birch", top="smooth_quartz")
    # bedroom east behind a frosted glass wall
    partition(d, 11, 7, 11, 11, y0, 4, "white_concrete", ((11, 7, "east"),), "birch")
    for z in (8, 10):
        d.set(11, 3, z, "light_gray_stained_glass_pane")
    d.fill(12, y0, 12, 14, 4, 12, "white_concrete")
    d.set(12, 3, 12, "light_gray_stained_glass_pane")
    bedset(d, 14, y0, 9, "east", ("r",), "light_gray", "birch", light="end_rod[facing=up]")
    if L >= 2:
        d.bed(14, y0, 10, "east", "light_gray")
    else:
        nightstand(d, 14, y0, 10, "birch", "end_rod[facing=up]")
    rugc(d, 12, 8, 12, 10, y0, "cyan")
    # stair (L3+): along the back wall rising west to the upper landing
    if up:
        ux1, ux2, uz1, uz2 = 5, 18, 5, 15
        flight(d, 14, 14, y0, 5, "west", "smooth_quartz")
        nt_box(d, ux1, uz1, ux2, uz2, 7, 9)
        d.fill(ux1, 6, uz1, ux2, 6, uz2, "light_gray_concrete")
        for x, z in cells(11, 14, 13, 14):
            d.set(x, 6, z, AIR)
        d.clear(ux1 + 1, 7, uz1 + 1, ux2 - 1, 9, uz2 - 1)
        d.fill(ux1, 10, uz1, ux2, 10, uz2, "smooth_quartz")
        for x, z in cells(ux1, uz1, ux2, uz2):
            if x in (ux1, ux2) or z in (uz1, uz2):
                d.set(x, 11, z, slab("smooth_quartz"))
        for x in range(ux1, ux2 + 1):
            d.set(x, 6, uz1, "cyan_terracotta")
        # bedroom wing glazing (north) – a ribbon of glass
        for x in range(ux1 + 1, ux2):
            if x not in (9, 13):
                d.window(x, 7, uz1, x, 9, uz1, "glass_pane")
        for z in (8, 11):
            d.window(ux1, 8, z, ux1, 9, z)
        for x in (8, 15):
            d.window(x, 8, uz2, x, 9, uz2)
        # rooms: walls at x=9 and x=13 (z6..11), corridor wall z=12
        partition(d, ux1 + 1, 12, ux2 - 1, 12, 7, 9, "white_concrete",
                  ((7, 12, "north"), (11, 12, "north"), (15, 12, "north")), "birch")
        d.fill(9, 7, uz1 + 1, 9, 9, 11, "white_concrete")
        d.fill(13, 7, uz1 + 1, 13, 9, 11, "white_concrete")
        bedset(d, 7, 7, 6, "north", ("l", "r"), "cyan", "birch", light="end_rod[facing=up]")
        if L >= 4:
            bedset(d, 11, 7, 6, "north", ("l", "r"), "light_blue", "birch", light="end_rod[facing=up]")
        else:
            d.set(11, 7, 6, "smooth_quartz_slab[type=top,waterlogged=false]")
            d.chair(11, 7, 7, "south", "birch", sit=False)
            d.set(10, 7, 6, "potted_bamboo")
        sofa(d, 16, 13, 7, 2, "south", "east", "birch", arms=False)
        d.set(15, 7, 14, "smooth_quartz_slab[type=bottom,waterlogged=false]")
        if L >= 5:
            bedset(d, 15, 7, 6, "north", ("l", "r"), "lime", "birch", light="end_rod[facing=up]")
        else:
            d.set(16, 7, 6, "smooth_quartz_slab[type=top,waterlogged=false]")
            d.chair(16, 7, 7, "south", "birch", sit=False)
            d.set(15, 7, 6, "potted_bamboo")
        for x in (6, 10, 14):
            wardrobe(d, x, 7, 11, "east" if x != 14 else "east", "birch")
        for x in (7, 11, 15):
            d.set(x, 10, 9, "sea_lantern")
            d.set(x, 10, 14, "sea_lantern")
        d.set(6, 7, 14, "potted_bamboo")
        # glass balustrade at the stair hole
    # ---- L2 garage workshop (east), under the cantilever from L3
    if L >= 2:
        gx1, gx2, gz1, gz2 = x2, 20, 8, 15
        nt_box(d, gx1, gz1, gx2, gz2, y0, 5, "light_gray_concrete", "light_gray_concrete")
        d.fill(gx1 + 1, 1, gz1 + 1, gx2 - 1, 1, gz2 - 1, "polished_andesite")
        d.clear(gx1 + 1, y0, gz1 + 1, gx2 - 1, 5, gz2 - 1)
        for x, z in cells(gx1, gz1, gx2, gz2):
            if d.air(x, 6, z):
                d.set(x, 6, z, "smooth_quartz")
        for x in range(gx1 + 1, gx2):
            d.window(x, y0, gz1, x, 4, gz1, "light_gray_stained_glass_pane")
        d.door(gx1 + 2, y0, gz1, "south", "birch")
        d.door(gx1, y0, 13, "east", "birch")
        d.item(16, y0, gz2 - 1, "smithing_table")
        d.item(17, y0, gz2 - 1, "anvil", "east")
        d.item(18, y0, gz2 - 1, "grindstone", "east")
        d.item(19, y0, gz2 - 1, "crafting_table")
        d.item(19, y0, gz2 - 2, "barrel", "west")
        d.set(19, y0, 11, "chest[facing=west,type=single,waterlogged=false]")
        d.set(17, 5, 12, "sea_lantern")
        if L < 3:
            for x, z in cells(gx1, gz1, gx2, gz2):
                if x in (gx1, gx2) or z in (gz1, gz2):
                    d.set(x, 7, z, slab("smooth_quartz"))
    # ---- L5 roof terrace on the garage + jukebox / ender chest
    if L >= 5:
        d.door(18, 7, 12, "east", "birch")
        for x, z in cells(19, 9, 20, 15):
            d.set(x, 7, z, AIR)
        for z in range(8, 16):
            d.set(20, 7, z, "glass_pane")
        for x in (19, 20):
            d.set(x, 7, 8, "glass_pane")
            d.set(x, 7, 15, "glass_pane")
        d.chair(19, 7, 10, "north", "birch", sit=False)
        planter(d, 19, 14, 19, 14, 6)
        d.item(15, 7, 14, "jukebox")
        d.item(4, y0, 13, "ender_chest", "east")
    # front terrace with planters
    planter(d, x1, z1 - 3, x1 + 2, z1 - 3, 1, ("azalea", "fern", "flowering_azalea"))
    planter(d, 13, z1 - 3, x2, z1 - 3, 1, ("azalea", "fern", "flowering_azalea"))
    return d




# ============================================================================================ COTTAGE
def dormer(d, c, z, y, out, wall, roofb, glass="glass_pane"):
    """Small gabled dormer on a roof slope: window at (c, y, z) in the slope facing `out` (north/south)."""
    ox, oz = D4[out]
    d.set(c, y, z, glass)
    d.set(c - 1, y, z, wall)
    d.set(c + 1, y, z, wall)
    d.set(c, y + 1, z, wall)
    d.set(c - 1, y + 1, z, stair(roofb, "east"))
    d.set(c + 1, y + 1, z, stair(roofb, "west"))
    d.set(c, y + 2, z, slab(roofb))
    d.set(c - 1, y + 1, z + oz, stair(roofb, "east"))
    d.set(c + 1, y + 1, z + oz, stair(roofb, "west"))
    d.set(c, y + 2, z + oz, slab(roofb))
    d.set(c, y + 1, z + oz, wall)


def cottage_hw(rel, L, v=0):
    d = Design("Hearthwood", rel, (21, 22, 22), paving="grass_block[snowy=false]")
    x1, x2, z1, z2 = 4, 14, 7, 14
    y0 = 2
    stone, quoin, R = "smooth_sandstone", "cut_sandstone", "deepslate_tile"
    brick_walls(d, x1, z1, x2, z2, y0, 6, stone, "stone_bricks", quoin)
    d.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, z2 - 1, "spruce_planks")
    d.clear(x1 + 1, y0, z1 + 1, x2 - 1, 6, z2 - 1)
    d.fill(x1 + 1, 5, z1 + 1, x2 - 1, 5, z2 - 1, "spruce_planks")        # attic floor
    ridge = d.gable(x1, z1, x2, z2, 7, "x", "deepslate_tile_stairs", "deepslate_tile_slab", stone)
    for x in range(x1 - 1, x2 + 2):
        for z in (10, 11):
            d.set(x, ridge, z, "deepslate_tiles")
    # openings
    d.door(9, y0, z1, "south", "dark_oak")
    d.set(9, y0 + 2, z1, quoin)
    for x in (8, 9, 10):
        d.set(x, y0 + 3, z1 - 1, slab(R))
    d.set(8, y0 + 2, z1 - 1, stair("stone_brick", "south", "top"))
    d.set(10, y0 + 2, z1 - 1, stair("stone_brick", "south", "top"))
    for xs in ((6, 7), (11, 12)):
        for x in xs:
            hw_window(d, x, 3, z1, 1)
            d.set(x, 4, z1, quoin)
        d.flowerbox(xs[0], z1 - 1, xs[1], z1 - 1, y0, ("red_tulip", "pink_tulip", "allium"))
    for x in (6, 12):
        hw_window(d, x, 3, z2, 1)
    hw_window(d, x1, 3, 11, 1)
    hw_window(d, x1, 6, 11, 2)
    hw_window(d, x2, 7, 10, 1)
    if L >= 3:                                                             # front dormers
        dormer(d, 6, z1, 7, "north", stone, R)
        dormer(d, 12, z1, 7, "north", stone, R)
    # central stair between the two ground rooms (hall at z=8)
    flight(d, 9, 9, y0, 4, "south", "dark_oak", support="spruce_planks")
    for xw in (8, 10):
        d.fill(xw, y0, 9, xw, 4, z2 - 1, "spruce_planks")
        for z in range(z1 + 1, z2):
            for y in range(6, 11):
                if d.air(xw, y, z):
                    d.set(xw, y, z, "spruce_planks")
                else:
                    break
    d.door(8, 6, z2 - 1, "west", "spruce")
    d.door(10, 6, z2 - 1, "east", "spruce")
    d.set(9, 6, z1 + 1, "chest[facing=south,type=single,waterlogged=false]")
    d.set(9, 4, z1 + 1, "lantern[hanging=true,waterlogged=false]")
    # ---- west room: kitchen + table for two
    d.hut(5, y0, 9)
    kitchen(d, [(5, 10, "furnace"), (5, 11, "sink"), (5, 12, "smoker")], y0, "east", "dark_oak")
    kitchen(d, [(6, 13, "crafting_table"), (7, 13, "barrel")], y0, "north", "dark_oak")
    if L in (2, 3, 4):
        d.item(5, y0, 13, "barrel", "up")
    else:
        d.set(5, y0, 13, "composter[level=3]")
    d.table(7, y0, 10, "dark_oak")
    d.chair(7, y0, 9, "north", "dark_oak", sit=False)
    d.chair(7, y0, 11, "south", "dark_oak", sit=False)
    d.lamp(6, 4, 11)
    # ---- east room: parlour with inglenook
    fireplace(d, x2, 11, y0, "west", ridge + 3, "stone_bricks", "stone_bricks")
    if v == 0:      # two armchairs at the inglenook
        d.chair(12, y0, 10, "west", "dark_oak", arms=False)
        d.chair(12, y0, 12, "west", "dark_oak", arms=False)
        rugc(d, 13, 10, 13, 12, y0, "green")
    else:           # neighbour's cottage: a settle across the hearth and a footstool
        sofa(d, 12, 10, y0, 3, "south", "west", "spruce", arms=False)
        rugc(d, 13, 10, 13, 12, y0, "blue")
        d.set(11, y0, 9, "potted_cornflower")
    d.set(13, 3, 10, AIR)
    if L >= 3:
        d.bookshelf(11, y0, 13)
        d.item(13, y0, 13, "lectern", "north")
    else:
        d.set(11, y0, 13, "potted_fern")
    if L >= 5:
        d.item(11, y0, 9, "jukebox")
    d.lamp(12, 4, 11)
    if L < 3:                                              # east attic: sewing and writing room
        d.set(13, 6, 9, slab("spruce", "top"))
        d.set(13, 7, 9, "candle[candles=2,lit=false,waterlogged=false]")
        d.chair(12, 6, 9, "west", "spruce", sit=False)
        d.set(13, 6, 11, "loom[facing=west]")
        d.set(11, 6, 9, "bookshelf")
    # ---- attic bedrooms
    bedset(d, 5, 6, 9, "west", ("r",), "white", "spruce")
    if L >= 2:
        d.bed(5, 6, 11, "west", "white")
    if L >= 3:
        bedset(d, 13, 6, 9, "east", ("l",), "yellow", "spruce")
    if L >= 4:
        d.bed(13, 6, 11, "east", "yellow")
    wardrobe(d, 5, 6, 13, "east", "spruce")
    wardrobe(d, 13, 6, 13, "west", "spruce")
    # ---- garden: picket fence, flower borders, path, a bench and an apple tree corner
    garden(d, 1, 0, 8, z1 - 3, y0, "spruce", ((8, 2, "east"),),
           plants=((2, 1, "rose_bush[half=lower]"), (3, 1, "poppy"), (6, 1, "oxeye_daisy"), (2, 3, "cornflower"),
                   (4, 3, "allium"), (6, 3, "lilac[half=lower]")))
    garden(d, 10, 0, 19, z1 - 3, y0, "spruce", ((10, 2, "west"),),
           plants=((12, 1, "red_tulip"), (14, 1, "peony[half=lower]"), (18, 1, "dandelion"), (12, 3, "azure_bluet"),
                   (17, 3, "cornflower")))
    for z in range(0, z1):
        d.set(9, 1, z, "gravel")
    clear_above_path(d, [(9, z) for z in range(0, z1)], 1)
    d.set(3, y0, 2, "flowering_azalea")
    d.set(16, y0, 2, "rose_bush[half=lower]")
    d.set(16, y0 + 1, 2, "rose_bush[half=upper]")
    # ---- L2 scullery lean-to on the west gable, L5 garden bedroom lean-to at the back
    if L >= 2:
        sx1 = 1
        brick_walls(d, sx1, 9, x1, 13, y0, 4, stone, "stone_bricks")
        d.clear(sx1 + 1, y0, 10, x1 - 1, 4, 12)
        d.fill(sx1 + 1, 1, 10, x1 - 1, 1, 12, "stone_bricks")
        shed_roof(d, sx1, 9, x1 - 1, 13, 5, "west", R)
        for z in (9, 13):
            for x in range(sx1 + 1, x1):
                for y in range(5, 5 + (x - sx1)):
                    d.set(x, y, z, stone)
        d.set(x1, y0, 11, AIR)
        d.set(x1, y0 + 1, 11, AIR)
        d.set(2, y0, 10, "water_cauldron[level=3]")
        d.set(2, y0, 12, "barrel[facing=up,open=false]")
        d.set(3, y0, 12, "barrel[facing=east,open=false]")
        hw_window(d, sx1, 3, 11, 1)
        d.set(2, 4, 11, "lantern[hanging=true,waterlogged=false]")
    if L >= 5:
        bx1, bx2, bz1, bz2 = 10, 16, z2, 19
        brick_walls(d, bx1, bz1, bx2, bz2, y0, 4, stone, "stone_bricks", quoin)
        d.clear(bx1 + 1, y0, bz1 + 1, bx2 - 1, 4, bz2 - 1)
        d.fill(bx1 + 1, 1, bz1 + 1, bx2 - 1, 1, bz2 - 1, "spruce_planks")
        d.gable(bx1, bz1 + 2, bx2, bz2, 5, "z", "deepslate_tile_stairs", "deepslate_tile_slab", stone)
        d.door(bx2, y0, 17, "west", "dark_oak")
        hw_window(d, 13, 3, bz2, 1)
        bedset(d, 12, y0, bz2 - 1, "south", ("l",), "pink", "spruce")
        d.chair(14, y0, bz2 - 1, "south", "spruce", sit=False)
        d.lamp(13, 4, 17)
        for x in range(bx2 + 1, 20):
            d.set(x, 1, 17, "gravel")
    return d


def aframe(d, x1, x2, z1, z2, y, stairb="dark_oak", full="dark_oak_planks", overhang=1):
    """Steep A-frame (2 up per 1 across) over x1..x2, ridge along z. Returns ridge y."""
    half = (x2 - x1) // 2
    for x in range(x1, x2 + 1):
        j = min(x - x1, x2 - x)
        face = "east" if x - x1 < half else "west"
        for z in range(z1 - overhang, z2 + overhang + 1):
            if j == half:
                d.set(x, y + 2 * j, z, full)
                d.set(x, y + 2 * j + 1, z, slab(stairb))
            else:
                d.set(x, y + 2 * j, z, full)
                d.set(x, y + 2 * j + 1, z, stair(stairb, face))
    return y + 2 * half + 1


def cottage_ca(rel, L, v=0):
    d = Design("Cascadia", rel, (23, 24, 25), paving="grass_block[snowy=false]")
    W = "spruce"
    x1, x2, z1, z2 = 4, 18, 9, 19
    y0 = 2
    mid = 11
    ridge = aframe(d, x1, x2, z1, z2, y0)
    for x, z in cells(x1, z1, x2, z2):
        d.set(x, 1, z, "spruce_planks" if x1 < x < x2 and z1 < z < z2 else "cobblestone")
    # glazed street gable and a planked back gable with stripped-log framing
    for x in range(x1 + 1, x2):
        j = min(x - x1, x2 - x)
        for y in range(y0, y0 + 2 * j):
            d.set(x, y, z1, "glass_pane" if (x not in (mid - 3, mid + 3) and y != 7) else
                  log("stripped_spruce_log", "y" if y != 7 else "x"))
            d.set(x, y, z2, "spruce_planks" if y != 7 else log("stripped_spruce_log", "x"))
    d.door(mid, y0, z1, "south", W)
    d.set(mid, y0 + 2, z1, log("stripped_spruce_log", "x"))
    for x in (mid - 1, mid + 1):
        for y in (y0, y0 + 1, y0 + 2):
            d.set(x, y, z1, log("stripped_spruce_log", "y"))
    for x in (8, 14):
        d.window(x, 9, z2, x, 10, z2)
    d.window(16, 3, z2, 16, 3, z2)
    # front deck
    for x, z in cells(x1 - 1, 3, x2 + 1, z1 - 1):
        d.set(x, 1, z, "spruce_planks")
    for x, z in cells(x1 - 1, 3, x2 + 1, z1 - 1):
        if (x in (x1 - 1, x2 + 1) or z == 3) and abs(x - mid) > 1:
            d.set(x, y0, z, fence(W))
    for x in (mid - 1, mid, mid + 1):
        d.set(x, 1, 2, stair("spruce", "south"))
        for z in (0, 1):
            d.set(x, 1, z, "coarse_dirt" if (x + z) % 2 else "gravel")
    d.chair(7, y0, 5, "south", W, sit=False, arms=True)
    d.chair(15, y0, 5, "south", W, sit=False, arms=True)
    for x in (x1 - 1, x2 + 1):
        d.set(x, y0 + 1, 3, lantern(False))
    # ---- ground: kitchen under the west slope, hearth on the back wall, bed under the east slope
    d.hut(6, y0, z1 + 1)
    kitchen(d, [(5, 13, "furnace"), (5, 14, "sink"), (5, 15, "smoker"), (5, 16, "crafting_table"),
                (5, 17, "barrel")], y0, "east", W, shelf=False)
    if 2 <= L <= 4:
        d.item(5, y0, 18, "barrel", "east")
    if v == 0:
        d.table(7, y0, 15, W)
        d.chair(7, y0, 14, "north", W, sit=False)
        d.chair(7, y0, 16, "south", W, sit=False)
    else:           # lodge: bigger table for the guests by the glass
        d.dining(8, y0, 12, 2, "x", W, ("n", "s"), sit=False)
    fireplace(d, mid, z2, y0, "north", ridge + 2, "cobblestone", "mossy_cobblestone")
    for y in range(y0 + 2, ridge + 2):
        d.set(mid, y, z2 + 1, "cobblestone" if y % 4 else "mossy_cobblestone")
    if v == 0:
        rugc(d, 10, 17, 12, 18, y0, "red")
        sofa(d, 10, 16, y0, 3, "east", "north", W)
    else:           # lodge: two armchairs and a bearskin-brown rug at the hearth
        rugc(d, 10, 17, 12, 18, y0, "brown")
        d.chair(10, y0, 16, "north", W)
        d.chair(12, y0, 16, "north", W)
        d.set(11, y0, 16, slab(W))
    bedset(d, 17, y0, 18, "south", (), "red", W)
    nightstand(d, 16, y0, 18, W, "lantern")
    d.set(17, y0, 16, "chest[facing=north,type=single,waterlogged=false]")
    if L >= 3:
        d.bookshelf(17, y0, 10)
        d.item(17, y0, 11, "lectern", "west")
        d.chair(15, y0, 11, "east", W, sit=False)
    if L >= 5:
        d.item(17, y0, 12, "jukebox")
    # chain lantern from the ridge
    for y in range(13, ridge - 1):
        d.set(mid, y, 12, "chain[axis=y,waterlogged=false]")
    d.set(mid, 12, 12, lantern(True))
    # ---- sleeping loft (L2+)
    if L >= 2:
        d.fill(8, 6, 15, 14, 6, z2 - 1, "spruce_planks")
        flight(d, 14, 10, y0, 5, "south", W)
        for x in range(8, 14):
            d.set(x, 7, 15, fence(W))
        bedset(d, 8, 7, 18, "south", (), "green", W)
        if L >= 3:
            d.bed(9, 7, 18, "south", "green")
        nightstand(d, 10, 7, 18, W, "lantern")
        if L >= 4:
            d.bed(12, 7, 18, "south", "lime")
        if L >= 5:
            d.bed(13, 7, 18, "south", "lime")
        nightstand(d, 11, 7, 18, W, "candle")
        d.set(14, 7, 18, "chest[facing=north,type=single,waterlogged=false]")
        rugc(d, 9, 16, 12, 16, 7, "brown")
    # ---- L4 fire pit with log benches beside the deck
    if L >= 4:
        for x, z in cells(19, 9, 22, 13):
            d.set(x, 1, z, "coarse_dirt")
        d.set(21, 1, 11, "cobblestone")
        d.set(21, y0, 11, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        d.set(21, y0, 9, log("spruce_log", "x"))
        d.set(22, y0, 9, log("spruce_log", "x"))
        d.set(21, y0, 13, log("spruce_log", "x"))
        d.set(22, y0, 13, log("spruce_log", "x"))
    return d


def cottage_nt(rel, L, v=0):
    d = Design("Neoterra", rel, (21, 20, 23), paving="grass_block[snowy=false]")
    W = "birch"
    x1, x2, z1, z2 = 4, 14, 5, 12
    y0 = 2
    slat = log("stripped_birch_log", "y")
    nt_box(d, x1, z1, x2, z2, y0, 5, slat, "white_concrete")
    d.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, z2 - 1, "birch_planks")
    d.clear(x1 + 1, y0, z1 + 1, x2 - 1, 5, z2 - 1)

    def green_roof(a1, b1, a2, b2, y):
        d.fill(a1, y, b1, a2, y, b2, "smooth_quartz")
        for x, z in cells(a1, b1, a2, b2):
            if x in (a1, a2) or z in (b1, b2):
                d.set(x, y + 1, z, slab("smooth_quartz"))
            else:
                d.set(x, y + 1, z, "moss_block" if (x + z) % 4 else "grass_block[snowy=false]")
                if (x * 3 + z) % 7 == 0:
                    d.set(x, y + 2, z, "azalea")
                elif (x + z * 5) % 9 == 0:
                    d.set(x, y + 2, z, "flowering_azalea")
                elif (x + z) % 3 == 0:
                    d.set(x, y + 2, z, "short_grass")
    green_roof(x1 - 1, z1 - 1, x2 + 1, z2, 6)
    for x in range(x1 + 1, x2):
        if x != 9:
            d.window(x, y0, z1, x, 4, z1)
    d.door(9, y0, z1, "south", W)
    d.fill(x1 + 1, 5, z1, x2 - 1, 5, z1, "white_concrete")
    for z in (8, 10):
        d.window(x2, 3, z, x2, 4, z)
    d.window(7, 3, z2, 8, 4, z2)
    # ---- open plan
    fireplace(d, x1, 8, y0, "east", 9, "polished_blackstone_bricks", fire="soul_campfire")
    if v == 0:      # sofa facing the linear fire
        rugc(d, 5, 7, 6, 9, y0, "light_gray")
        sofa(d, 7, 7, y0, 3, "south", "east", W, arms=False)
    elif v == 1:    # two armchairs and a small table for two by the window
        rugc(d, 5, 7, 6, 9, y0, "cyan")
        fit(d, [(6, y0, 7, stair(W, "east")), (6, y0, 9, stair(W, "east")), (8, y0, 8, slab("smooth_quartz", "top")),
                (8, y0 + 1, 8, "potted_azure_bluet"), (8, y0, 7, stair(W, "north")), (8, y0, 9, stair(W, "south"))])
    elif v == 2:    # dining pavilion: table for four, rug, plant
        rugc(d, 5, 7, 5, 9, y0, "orange")
        d.dining(7, y0, 8, 2, "x", W, ("n", "s"), sit=False)
    elif v == 3:    # yoga / music room: mats, a lute (note block), plants
        rugc(d, 5, 7, 8, 9, y0, "lime")
        fit(d, [(9, y0, 9, "note_block[instrument=guitar,note=0,powered=false]"), (9, y0, 7, "potted_fern"),
                (5, y0, 10, "potted_bamboo")])
    else:           # painter's pavilion: easel, desk and stool
        rugc(d, 5, 8, 6, 9, y0, "magenta")
        fit(d, [(7, y0, 7, fence(W)),
                (7, y0 + 1, 7, "birch_trapdoor[facing=south,half=top,open=true,powered=false,waterlogged=false]"),
                (8, y0, 9, slab("smooth_quartz", "top")), (8, y0, 8, stair(W, "north")), (9, y0, 9, "potted_bamboo")])
    d.hut(5, y0, 6)
    kitchen(d, [(5, 11, "barrel"), (6, 11, "furnace"), (7, 11, "sink"), (8, 11, "smoker"),
                (9, 11, "crafting_table")], y0, "north", W, top="smooth_quartz")
    if 2 <= L <= 4:
        d.item(5, y0, 10, "barrel", "east")
    for x, z in ((6, 8), (8, 10), (12, 8)):
        d.set(x, 5, z, "sea_lantern")
    # sleeping nook behind a bookcase partition
    partition(d, 10, z1 + 1, 10, z2 - 1, y0, 4, "birch_planks", ((10, z1 + 1, "east"),), W)
    for z in (8, 9, 10):
        d.set(10, y0 + 1, z, "chiseled_bookshelf[facing=west,slot_0_occupied=true,slot_1_occupied=false,"
                              "slot_2_occupied=true,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")
    bedset(d, 13, y0, 8, "east", ("l",), "light_gray", W, light="end_rod[facing=up]")
    if L >= 2:
        d.bed(13, y0, 9, "east", "light_gray")
    nightstand(d, 13, y0, 10, W, "end_rod[facing=up]")
    if L >= 5:
        d.item(11, y0, 11, "jukebox")
    else:
        d.set(11, y0, 11, "potted_bamboo")
    # ---- garden: stepping stones, planters, a small pond
    for z in range(0, z1):
        d.set(9, 1, z, "smooth_stone" if z % 2 == 0 else "grass_block[snowy=false]")
    planter(d, 5, 2, 7, 2, 1)
    planter(d, 11, 2, 13, 2, 1)
    # ---- L3+ second pavilion with study and bedrooms, joined by a glass link
    if L >= 3:
        px1, px2, pz1, pz2 = 6, 16, 15, 20
        nt_box(d, px1, pz1, px2, pz2, y0, 5, slat, "white_concrete")
        d.fill(px1 + 1, 1, pz1 + 1, px2 - 1, 1, pz2 - 1, "birch_planks")
        d.clear(px1 + 1, y0, pz1 + 1, px2 - 1, 5, pz2 - 1)
        green_roof(px1 - 1, pz1, px2 + 1, pz2 + 1, 6)
        # link corridor
        for z in range(z2, pz1 + 1):
            d.set(12, 1, z, "polished_diorite")
            for y in range(y0, 5):
                d.set(11, y, z, "glass_pane")
                d.set(13, y, z, "glass_pane")
            d.set(12, y0, z, AIR)
            d.set(12, y0 + 1, z, AIR)
            d.set(12, y0 + 2, z, AIR)
            for x in (11, 12, 13):
                d.set(x, 5, z, "smooth_quartz")
                d.set(x, 6, z, slab("smooth_quartz")) if z not in (z2, pz1) else None
        d.door(12, y0, z2, "south", W)
        d.door(12, y0, pz1, "south", W)
        d.set(12, y0 + 2, z2, "white_concrete")
        d.set(12, y0 + 2, pz1, "white_concrete")
        for x in range(px1 + 1, px2):
            if x not in (11, 12, 13):
                d.window(x, 3, pz2, x, 4, pz2)
        d.window(px1, 3, 17, px1, 4, 18)
        d.window(px2, 3, 17, px2, 4, 18)
        # study (west): lectern, bookshelf, desk
        d.bookshelf(7, y0, 16)
        d.set(7, y0 + 1, 16, "bookshelf")
        d.item(7, y0, 18, "lectern", "east")
        d.set(9, y0, 16, slab("smooth_quartz", "top"))
        d.chair(9, y0, 17, "south", W, sit=False)
        d.set(9, 5, 18, "sea_lantern")
        # bedrooms (east)
        bedset(d, 14, y0, 19, "south", ("r",), "cyan", W, light="end_rod[facing=up]")
        if L >= 4:
            d.bed(13, y0, 19, "south", "cyan")
        if L >= 5:
            bedset(d, 11, y0, 19, "south", ("l",), "lime", W, light="end_rod[facing=up]")
        d.set(14, 5, 17, "sea_lantern")
        rugc(d, 12, 17, 14, 17, y0, "cyan")
    return d




# ============================================================================================ studio flat template
CCW = {v: k for k, v in CW.items()}


def flat(d, ox, oz, y, out, mirror=False, layout=None, wood=None, top=None, bedc=None, ceil=None, double=False,
         **_):
    """Draw one hand-written 7 x 6 flat layout. Local (0,0) is the interior corner on the window wall (`out` is
    the world direction of that wall); local x runs along the window wall (to CW[out], or CCW when mirrored),
    local z runs inward. `layout` is a list of placements from the per-pack tables below."""
    wood = wood or d.P["wood"]
    E = CCW[out] if mirror else CW[out]
    S = OPP[out]
    ex, ez = D4[E]
    sx, sz = D4[S]
    dirs = {"N": out, "S": S, "E": E, "W": OPP[E]}

    def W(lx, lz):
        return ox + ex * lx + sx * lz, oz + ez * lx + sz * lz
    taken = set()
    for it in layout:
        k, lx, lz = it[0], it[1], it[2]
        x, z = W(lx, lz)
        if (x, z) in taken:
            continue
        if k == "bed":
            d.bed(x, y, z, dirs[it[3]], bedc)
            if double and len(it) > 4:                     # a second bed beside the first (couple's room)
                dx2, dz2 = D4[dirs[it[4]]]
                d.bed(x + dx2, y, z + dz2, dirs[it[3]], bedc)
                fx, fz = D4[OPP[dirs[it[3]]]]
                taken |= {(x + dx2, z + dz2), (x + dx2 + fx, z + dz2 + fz)}
        elif k == "stand":
            nightstand(d, x, y, z, wood, it[3] if len(it) > 3 else "candle")
        elif k == "chest":
            d.set(x, y, z, f"chest[facing={dirs[it[3]]},type=single,waterlogged=false]")
        elif k == "shelf":
            d.set(x, y, z, f"chiseled_bookshelf[facing={dirs[it[3]]},slot_0_occupied=true,slot_1_occupied=false,"
                           f"slot_2_occupied=true,slot_3_occupied=true,slot_4_occupied=true,slot_5_occupied=false]")
        elif k == "item":
            name = it[3]
            d.item(x, y, z, name, dirs[it[4]] if len(it) > 4 and name != "crafting_table" else None)
        elif k == "sink":
            d.set(x, y, z, CAUL)
        elif k == "table":
            if top:
                d.set(x, y, z, slab(top, "top") if not top.endswith("_slab") else f"{top}[type=top,waterlogged=false]")
            else:
                d.table(x, y, z, wood)
        elif k == "chair":
            d.chair(x, y, z, dirs[it[3]], wood, it[4] if len(it) > 4 else True)
        elif k == "carpet":
            d.set(x, y, z, f"{it[3] if len(it) > 3 else (bedc or d.P['bed'])}_carpet")
        elif k == "set":
            d.set(x, y + (it[4] if len(it) > 4 else 0), z, it[3])
        elif k == "lamp" and ceil:
            d.set(x, ceil, z, LANT)
        elif k == "light" and ceil:
            d.set(x, ceil + 1, z, it[3])
    return W


# Hand-written flat layouts (local coords, see flat()). Entrances that must stay free: HW (6,5), NT (5,5) and the
# balcony door (4,0), CA boarding room and cabins (4,5).
HW_FLATS = [
    [  # parlour flat: bed by the window, kitchen down the side wall, round table, two armchairs and a rug
        ("bed", 0, 0, "N", "E"), ("stand", 1, 0), ("chest", 2, 0, "S"),
        ("item", 6, 0, "furnace", "W"), ("sink", 6, 1), ("item", 6, 2, "smoker", "W"), ("item", 6, 3, "crafting_table"),
        ("item", 6, 4, "barrel", "W"), ("table", 3, 2), ("chair", 3, 1, "N"), ("chair", 3, 3, "S"),
        ("chair", 2, 2, "W"), ("chair", 4, 2, "E"), ("chair", 0, 3, "W", False), ("chair", 0, 4, "W", False),
        ("carpet", 1, 3, "red"), ("carpet", 1, 4, "red"), ("set", 0, 5, "potted_red_tulip"), ("lamp", 3, 3),
        ("set", 1, 0, "potted_azure_bluet", 1)],
    [  # bedsit: kitchen under the window, bed against the side wall, table by the door, books at the corner
        ("shelf", 0, 0, "S"), ("shelf", 1, 0, "S"), ("sink", 2, 0), ("item", 3, 0, "furnace", "S"),
        ("item", 4, 0, "smoker", "S"), ("item", 5, 0, "crafting_table"), ("item", 6, 0, "barrel", "S"),
        ("bed", 0, 3, "W", "S"), ("stand", 0, 2), ("chest", 0, 4, "E"), ("table", 4, 3), ("chair", 4, 2, "N"),
        ("chair", 4, 4, "S"), ("chair", 3, 3, "W"), ("chair", 5, 3, "E"),
        ("carpet", 2, 1, "brown"), ("carpet", 3, 1, "brown"), ("carpet", 4, 1, "brown"), ("carpet", 5, 1, "brown"),
        ("set", 0, 5, "potted_fern"), ("lamp", 4, 3)],
]
NT_FLATS = [
    [  # open plan: galley on the side wall, island with stools, bed in the window corner, lounge chairs
        ("item", 0, 1, "furnace", "E"), ("sink", 0, 2), ("item", 0, 3, "smoker", "E"), ("item", 0, 4, "crafting_table"),
        ("item", 0, 5, "barrel", "E"), ("table", 2, 2), ("table", 2, 3), ("chair", 3, 2, "E"), ("chair", 3, 3, "E"),
        ("bed", 6, 0, "N", "W"), ("stand", 5, 0, "end_rod[facing=up]"), ("shelf", 3, 0, "S"),
        ("chair", 6, 3, "E"), ("chair", 6, 4, "E"), ("set", 0, 0, "potted_bamboo"),
        ("carpet", 4, 3, "cyan"), ("carpet", 4, 4, "cyan"), ("lamp", 4, 2)],
    [  # studio: bed and dresser on the window wall, kitchen wall, dining table for four, plant corner
        ("bed", 0, 0, "N", "E"), ("stand", 1, 0, "end_rod[facing=up]"), ("chest", 2, 0, "S"),
        ("item", 6, 0, "furnace", "W"), ("sink", 6, 1), ("item", 6, 2, "smoker", "W"), ("item", 6, 3, "crafting_table"),
        ("item", 6, 4, "barrel", "W"), ("table", 3, 3), ("chair", 3, 2, "N"), ("chair", 3, 4, "S"),
        ("chair", 2, 3, "W"), ("chair", 4, 3, "E"), ("set", 0, 5, "potted_bamboo"), ("set", 0, 3, "potted_fern"),
        ("carpet", 1, 2, "light_gray"), ("carpet", 1, 3, "light_gray"), ("lamp", 3, 3)],
]
CA_FLATS = [
    [  # boarding room: bed under the back window, stove-side kitchen, table, settle by the wall
        ("bed", 0, 0, "N", "E"), ("stand", 1, 0, "lantern"), ("chest", 2, 0, "S"),
        ("item", 6, 0, "furnace", "W"), ("sink", 6, 1), ("item", 6, 2, "smoker", "W"), ("item", 6, 3, "crafting_table"),
        ("item", 6, 4, "barrel", "W"), ("table", 3, 2), ("chair", 3, 1, "N"), ("chair", 3, 3, "S"),
        ("chair", 2, 2, "W"), ("chair", 4, 2, "E"), ("chair", 0, 3, "W", False), ("chair", 0, 4, "W", False),
        ("carpet", 1, 3, "brown"), ("carpet", 1, 4, "brown"), ("set", 0, 5, "potted_fern"), ("lamp", 3, 3)],
    [  # boarding room: kitchen along the back, bed on the side wall, table near the door, wash stand
        ("sink", 2, 0), ("item", 3, 0, "furnace", "S"), ("item", 4, 0, "smoker", "S"), ("item", 5, 0, "crafting_table"),
        ("item", 6, 0, "barrel", "S"), ("set", 0, 0, "barrel[facing=south,open=false]"),
        ("bed", 0, 3, "W", "S"), ("stand", 0, 2, "lantern"), ("chest", 0, 4, "E"), ("set", 0, 5, CAUL),
        ("table", 5, 3), ("chair", 5, 2, "N"), ("chair", 5, 4, "S"), ("chair", 6, 3, "E"), ("chair", 4, 3, "W"),
        ("carpet", 2, 1, "green"), ("carpet", 3, 1, "green"), ("carpet", 4, 1, "green"), ("lamp", 3, 2)],
]
CABINS = [
    [  # trapper's cabin
        ("bed", 0, 0, "N", "E"), ("stand", 1, 0, "lantern"), ("item", 2, 0, "barrel", "S"),
        ("item", 6, 0, "furnace", "W"), ("sink", 6, 1), ("item", 6, 2, "smoker", "W"), ("item", 6, 3, "crafting_table"),
        ("item", 6, 4, "barrel", "W"), ("table", 3, 3), ("chair", 3, 2, "N"), ("chair", 3, 4, "S"), ("chair", 2, 3, "W"),
        ("carpet", 1, 3, "brown"), ("carpet", 1, 4, "brown"), ("set", 0, 5, "potted_fern"), ("lamp", 3, 2)],
    [  # cook's cabin: range under the window, bed on the side, table by the door
        ("item", 2, 0, "barrel", "S"), ("item", 3, 0, "furnace", "S"), ("sink", 4, 0), ("item", 5, 0, "smoker", "S"),
        ("item", 6, 0, "crafting_table"), ("item", 6, 1, "barrel", "W"),
        ("bed", 0, 3, "W", "N"), ("stand", 0, 2, "lantern"), ("chest", 0, 4, "E"),
        ("table", 4, 3), ("chair", 4, 4, "S"), ("chair", 3, 3, "W"), ("chair", 5, 3, "E"),
        ("carpet", 2, 1, "red"), ("carpet", 3, 1, "red"), ("carpet", 4, 1, "red"), ("lamp", 4, 2)],
    [  # foreman's cabin: kitchen on the west wall, bed in the window corner, desk
        ("item", 0, 0, "furnace", "E"), ("sink", 0, 1), ("item", 0, 2, "smoker", "E"), ("item", 0, 3, "crafting_table"),
        ("item", 0, 4, "barrel", "E"), ("item", 0, 5, "barrel", "E"),
        ("bed", 6, 0, "N", "W"), ("stand", 5, 0, "lantern"), ("table", 3, 2), ("chair", 3, 1, "N"),
        ("chair", 3, 3, "S"), ("chair", 4, 2, "E"), ("set", 6, 4, "cartography_table"),
        ("carpet", 2, 4, "green"), ("carpet", 3, 4, "green"), ("lamp", 3, 3)],
    [  # family cabin: bed centred on the window wall with two stands, kitchen east, table west
        ("bed", 3, 0, "N", "E"), ("stand", 2, 0, "lantern"), ("stand", 4, 0, "candle"),
        ("item", 6, 0, "barrel", "W"), ("item", 6, 1, "furnace", "W"), ("sink", 6, 2), ("item", 6, 3, "smoker", "W"),
        ("item", 6, 4, "crafting_table"), ("item", 6, 5, "barrel", "W"),
        ("table", 1, 3), ("chair", 1, 2, "N"), ("chair", 1, 4, "S"), ("chair", 2, 3, "E"),
        ("set", 0, 5, "potted_fern"), ("carpet", 3, 3, "orange"), ("carpet", 4, 3, "orange"), ("lamp", 3, 3)],
]
BUNKS = [
    [  # ranch bunk cabin: two bunks under the window, a stove kitchen and a card table
        ("bed", 0, 0, "N"), ("stand", 1, 0, "lantern"), ("bed", 2, 0, "N"),
        ("item", 6, 0, "furnace", "W"), ("sink", 6, 1), ("item", 6, 2, "smoker", "W"), ("item", 6, 3, "crafting_table"),
        ("item", 6, 4, "barrel", "W"), ("table", 3, 3), ("chair", 3, 2, "N", False), ("chair", 2, 3, "W", False),
        ("set", 0, 4, "chest[facing=east,type=single,waterlogged=false]"), ("set", 0, 5, "potted_fern"), ("lamp", 3, 3)],
    [  # second bunk cabin: bunks along the side wall, kitchen along the back
        ("item", 2, 0, "furnace", "S"), ("sink", 3, 0), ("item", 4, 0, "smoker", "S"), ("item", 5, 0, "crafting_table"),
        ("item", 6, 0, "barrel", "S"), ("bed", 0, 2, "W"), ("bed", 0, 4, "W"), ("stand", 0, 3, "lantern"),
        ("table", 5, 3), ("chair", 5, 4, "S", False), ("chair", 6, 3, "E", False),
        ("set", 0, 0, "potted_fern"), ("carpet", 3, 2, "lime"), ("carpet", 4, 2, "lime"), ("lamp", 4, 3)],
]

# ============================================================================================ APARTMENT
def apartment_nt(rel, L, F=None, v=0):
    F = F or L
    d = Design("Neoterra", rel, (17, 12 + 5 * F, 21), paving="smooth_stone")
    x1, x2, z1, z2 = 3, 11, 5, 16
    H = 5
    yt = 2 + H * F                                   # roof deck y (= walk of the would-be next floor - 1)
    for f in range(F):
        Y = 2 + H * f
        nt_box(d, x1, z1, x2, z2, Y, Y + H - 2)
        d.fill(x1, Y - 1, z1, x2, Y - 1, z2, "light_gray_concrete" if f else "polished_andesite")
        d.clear(x1 + 1, Y, z1 + 1, x2 - 1, Y + H - 2, z2 - 1)
        if f:
            d.fill(x1 + 1, Y - 1, z1 + 1, x2 - 1, Y - 1, z2 - 1, "polished_diorite")
            for x in range(x1, x2 + 1):
                d.set(x, Y - 1, z1, "cyan_terracotta")
        # flat (north), corridor wall z=12, corridor z=13, stair core z=14..15
        W = flat(d, x1 + 1, z1 + 1, Y, "north", layout=NT_FLATS[(f + v) % 2], wood="birch", top="smooth_quartz",
                 bedc=("cyan", "light_blue", "lime", "white")[(f + v) % 4], ceil=Y + 3)
        partition(d, x1 + 1, 12, x2 - 1, 12, Y, Y + 3, "white_concrete", ((9, 12, "north"),), "birch")
        for bx, col in ((5, "cyan"), (7, "light_gray")):                 # corridor art and a shelf
            d.set(bx, Y + 2, 13, f"{col}_wall_banner[facing=south]")
        d.set(6, Y + 2, 13, slab("smooth_quartz", "top"))
        d.set(6, Y + 3, 13, "potted_bamboo")
        # street glazing, side strip windows
        for x in range(x1 + 1, x2):
            d.window(x, Y, z1, x, Y + 3, z1)
        d.set(x1, Y + 3, z1, "light_gray_concrete")
        for z in (8, 10):
            d.window(x1, Y + 1, z, x1, Y + 2, z)
            d.window(x2, Y + 1, z, x2, Y + 2, z)
        d.window(x2, Y + 1, 14, x2, Y + 2, 15, "light_gray_stained_glass_pane")
        d.window(5, Y + 1, z2, 9, Y + 2, z2, "light_gray_stained_glass_pane")
        if f:
            # balcony with glass railing and a door from the flat
            for x in range(x1 + 1, x2):
                d.set(x, Y - 1, z1 - 1, "smooth_quartz")
                d.set(x, Y - 1, z1 - 2, "smooth_quartz")
                d.set(x, Y, z1 - 2, "glass_pane")
            for z in (z1 - 2, z1 - 1):
                d.set(x1 + 1, Y, z, "glass_pane")
                d.set(x2 - 1, Y, z, "glass_pane")
            d.door(8, Y, z1, "south", "birch")
            d.set(8, Y + 2, z1, "glass_pane")
            d.set(5, Y, z1 - 1, "potted_bamboo")
            if f % 2:
                d.set(9, Y, z1 - 1, "azalea")
    # stair core: alternate rows z=15 (rise east) / z=14 (rise west)
    for f in range(F - 1 + (1 if F >= 4 else 0)):
        Y = 2 + H * f
        if f % 2 == 0:
            flight(d, 5, 15, Y, H, "east", "smooth_quartz")
        else:
            flight(d, 9, 14, Y, H, "west", "smooth_quartz")
        d.set(7, Y + 3, 13, "sea_lantern")
    # roof
    if F >= 4:
        d.fill(x1, yt - 1, z1, x2, yt - 1, z2, "smooth_quartz")
        top_f = F - 1
        Y = 2 + H * top_f
        # re-open the last flight's well through the roof deck and build a stair hut
        if top_f % 2 == 0:
            for x in range(6, 10):
                d.set(x, yt - 1, 15, AIR)
        else:
            for x in range(5, 9):
                d.set(x, yt - 1, 14, AIR)
        for x, z in cells(x1, z1, x2, z2):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, yt, z, "glass_pane" if z in (z1,) or x in (x1, x2) and z < 13 else "white_concrete")
        nt_box(d, 4, 13, 10, z2, yt, yt + 2, "white_concrete", "white_concrete")
        d.clear(4, yt, 14, 10, yt + 2, 15)
        d.fill(3, yt + 3, 12, 11, yt + 3, z2, "smooth_quartz_slab[type=bottom,waterlogged=false]")
        d.door(7, yt, 13, "north", "birch")
        # terrace: planters, loungers, pergola lights
        for x in range(x1 + 1, x2):
            d.set(x, yt, z1 + 1, "moss_block" if x % 2 else "flowering_azalea")
        d.chair(5, yt, 9, "west", "birch", sit=False)
        d.chair(5, yt, 10, "west", "birch", sit=False)
        d.table(6, yt, 9, "birch", "slab", "smooth_quartz_slab")
        d.chair(9, yt, 9, "east", "birch", sit=False)
        d.chair(9, yt, 10, "east", "birch", sit=False)
        d.set(7, yt, 11, "lantern[hanging=false,waterlogged=false]")
        # solar panels on the stair hut
        for x in range(4, 11):
            d.set(x, yt + 4, 14, "daylight_detector[inverted=false,power=0]")
    else:
        d.flat(x1, z1, x2, z2, yt - 1, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
        for x in range(5, 10):
            d.set(x, yt, 14, "daylight_detector[inverted=false,power=0]")
    # ---- ground floor: side entrance with canopy and lobby details
    d.door(x1, 2, 13, "west", "birch")
    d.set(x1, 4, 13, "glass_pane")
    for z in (12, 13, 14):
        d.set(x1 - 1, 5, z, slab("smooth_quartz", "top"))
    d.sign(x1 - 1, 4, 12, "west", ["", "SKYLINE", "RESIDENCES"], "birch", glow=True, color="cyan")
    d.hut(10, 2, 13)
    if L >= 5:
        d.item(10, 2, 14, "ender_chest", "west")
    planter(d, 0, 6, 1, 11, 1)
    for x in range(x1, x2 + 1):
        d.set(x, 1, z1 - 2, "moss_block" if x % 3 else "grass_block[snowy=false]")
        if x % 2:
            d.set(x, 2, z1 - 2, "azalea") if x not in (x1, x2) else None
    return d


def apartment_hw(rel, L, F=None, garden_on=None, v=0):
    F = F or {1: 1, 2: 2, 3: 2, 4: 3, 5: 3}[L]
    garden_on = (L >= 2) if garden_on is None else garden_on
    d = Design("Hearthwood", rel, (27, 14 + 4 * F, 19), paving="grass_block[snowy=false]")
    x1, x2, z1, z2 = 3, 23, 5, 12
    H = 4
    yt = 2 + H * F
    for f in range(F):
        Y = 2 + H * f
        brick_walls(d, x1, z1, x2, z2, Y, Y + 2, "bricks", None, None)
        d.fill(x1 + 1, Y - 1, z1 + 1, x2 - 1, Y - 1, z2 - 1, "oak_planks" if f else "spruce_planks")
        d.clear(x1 + 1, Y, z1 + 1, x2 - 1, Y + 2, z2 - 1)
        for x, z in cells(x1, z1, x2, z2):                          # stone string course at every floor
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, Y - 1, z, "stone_bricks")
        for xw in (11, 15):
            d.fill(xw, Y, z1 + 1, xw, Y + 2, z2 - 1, "bricks")
        d.door(11, Y, 11, "west", "dark_oak")
        d.door(15, Y, 11, "east", "dark_oak")
        flat(d, 4, 6, Y, "north", False, HW_FLATS[(f + v) % 2], "dark_oak", None,
             ("red", "green", "yellow")[(f + v) % 3], Y + 2)
        flat(d, 22, 6, Y, "north", True, HW_FLATS[(f + v + 1) % 2], "dark_oak", None,
             ("blue", "brown", "purple")[(f + v) % 3], Y + 2)
        for x in (6, 8, 10, 16, 18, 20):                             # sash windows
            d.window(x, Y + 1, z1, x, Y + 2, z1)
        for x in (6, 8, 18, 20):
            d.window(x, Y + 1, z2, x, Y + 2, z2)
        for x in (13,):
            if f:
                d.window(x, Y + 1, z1, x, Y + 2, z1)
        d.set(13, Y + 2, 9, lantern(True))
        d.set(12, Y + 2, 6, "red_wall_banner[facing=south]")
        d.set(14, Y + 2, 6, "red_wall_banner[facing=south]")
        if f:
            d.set(13, Y, 6, "potted_fern")
        if f and L >= 3:                                              # wrought-iron balconettes
            for x in (8, 18):
                d.set(x, Y, z1 - 1, "iron_bars")
                d.set(x, Y - 1, z1 - 1, slab("stone_brick", "top"))
    for f in range(F - 1):
        Y = 2 + H * f
        if f % 2 == 0:
            flight(d, 14, 7, Y, H, "south", "dark_oak")
        else:
            flight(d, 12, 10, Y, H, "north", "dark_oak")
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):             # quoins
        for y in range(1, yt):
            if y % 2 == 0:
                d.set(x, y, z, "stone_bricks")
    d.fill(x1, yt - 1, z1, x2, yt - 1, z2, "stone_bricks")
    d.fill(x1 + 1, yt - 1, z1 + 1, x2 - 1, yt - 1, z2 - 1, "oak_planks")
    ridge = d.hip(x1, z1, x2, z2, yt, "deepslate_tile_stairs", "deepslate_tile_slab")
    for xw in (11, 15):                                               # party-wall chimney stacks
        for z in (8, 9):
            for y in range(yt, ridge + 3):
                d.set(xw, y, z, "bricks")
    if L >= 5:                                                        # attic dormers on the front slope
        for c in (7, 19):
            dormer(d, c, z1 + 1, yt + 1, "north", "bricks", "deepslate_tile")
    # entrance portico
    d.door(13, 2, z1, "south", "dark_oak")
    d.set(13, 4, z1, "stone_bricks")
    for x in (12, 14):
        for y in (2, 3, 4):
            d.set(x, y, z1 - 2, "stone_brick_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]"
                  if y < 4 else "chiseled_stone_bricks")
    for x in range(11, 16):
        for z in (z1 - 2, z1 - 1):
            d.set(x, 5, z, slab("stone_brick"))
    d.set(13, 1, z1 - 1, "stone_bricks")
    for z in range(0, z1 - 1):
        d.set(13, 1, z, "stone_bricks" if z % 2 else "polished_andesite")
    d.hut(12, 2, 8)
    if L >= 5:
        d.item(12, 2, 6, "ender_chest", "east")
    # front railings and a lamp post; back garden from L2
    for x in range(x1, x2 + 1):
        if abs(x - 13) > 1:
            d.set(x, 2, 1, "iron_bars")
    for x in (11, 15):
        d.set(x, 2, 1, "stone_brick_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
        d.set(x, 3, 1, lantern(False))
    if garden_on:
        garden(d, x1, z2 + 2, x2, 18, 2, "dark_oak", ((13, z2 + 2, "north"),),
               plants=((5, 15, "red_tulip"), (7, 17, "peony[half=lower]"), (16, 15, "allium"),
                       (19, 17, "rose_bush[half=lower]"), (21, 15, "oxeye_daisy")))
        for z in range(z2 + 1, 18):
            d.set(13, 1, z, "gravel")
        clear_above_path(d, [(13, z) for z in range(z2 + 1, 18)], 1)
        for x in (6, 20):
            d.set(x, 2, 16, "flowering_azalea")
        d.chair(9, 2, 17, "south", "dark_oak", sit=False)
        d.chair(10, 2, 17, "south", "dark_oak", sit=False)
    return d


def apartment_ca(rel, L, B=None, F=None, v=0):
    d = Design("Cascadia", rel, (31, 22, 19), paving="grass_block[snowy=false]")
    B = B or {1: 2, 2: 2, 3: 3, 4: 3, 5: 3}[L]
    F = F or (1 if L == 1 else 2)
    H = 5
    x1, z1, z2 = 3, 6, 13
    x2 = x1 + 8 * B
    yt = 2 + H * F
    for f in range(F):
        Y = 2 + H * f
        if f == 0:
            log_walls(d, x1, z1, x2, z2, Y, Y + 3, "stripped_spruce_log", "spruce_log")
        else:
            for y in range(Y, Y + 4):
                for x, z in cells(x1, z1, x2, z2):
                    if x in (x1, x2) or z in (z1, z2):
                        d.set(x, y, z, "spruce_planks")
        d.fill(x1 + 1, Y - 1, z1 + 1, x2 - 1, Y - 1, z2 - 1, "spruce_planks")
        d.clear(x1 + 1, Y, z1 + 1, x2 - 1, Y + 3, z2 - 1)
        for k in range(B + 1):
            xw = x1 + 8 * k
            d.fill(xw, Y, z1, xw, Y + 3, z2, "spruce_planks" if 0 < k < B else "stripped_spruce_log[axis=y]")
            for z in (z1, z2):
                d.fill(xw, Y, z, xw, Y + 3, z, log("spruce_log", "y"))
        for k in range(B):
            ox = x1 + 1 + 8 * k
            flat(d, ox, z2 - 1, Y, "south", True, CA_FLATS[(k + f + v) % 2], "spruce", None,
                 ("brown", "green", "orange", "red")[(k + f + v) % 4], Y + 3)
            d.door(ox + 4, Y, z1, "south", "spruce")
            ca_window(d, ox + 1, Y + 1, z1, "north", 2, w=2)
            for x in (ox + 3, ox + 5):
                ca_window(d, x, Y + 1, z2, "south", 2, shutters=False)
        # dark band at the floor line
        for x in range(x1, x2 + 1):
            for z in (z1, z2):
                d.set(x, Y + 4 if f < F - 1 else Y + 4, z, log("spruce_log", "x")) if f < F - 1 else None
    if F == 2:
        for x in range(x1, x2 + 1):
            for z in (z1, z2):
                d.set(x, 6, z, log("spruce_log", "x"))
    # roof
    d.fill(x1 + 1, yt - 1, z1 + 1, x2 - 1, yt - 1, z2 - 1, "spruce_planks")
    ridge = d.gable(x1, z1, x2, z2, yt, "x", "dark_oak_stairs", "dark_oak_slab", log("stripped_spruce_log", "z"))
    # stone chimney on the east gable
    for y in range(1, ridge + 3):
        for z in (9, 10):
            d.set(x2 + 1, y, z, "cobblestone" if (y + z) % 3 else "mossy_cobblestone")
    # porch (and two-storey gallery from L2)
    gy = 6 if F == 2 else None
    for x, z in cells(x1, 3, x2, z1 - 1):
        d.set(x, 1, z, "spruce_planks")
    top = yt - 1
    for x in range(x1, x2 + 1, 4):
        for y in range(2, top):
            d.set(x, y, 3, log("spruce_log", "y"))
        d.set(x, 1, 3, "cobblestone")
    if F == 2:
        for x, z in cells(x1, 3, x2, z1 - 1):
            d.set(x, 6, z, "spruce_planks")
        for x in range(x1, x2 + 1):
            if (x - x1) % 4:
                d.set(x, 7, 3, fence("spruce"))
        for x in range(x1 - 1, x2 + 2):
            for z in (2, 3, 4):
                d.set(x, top, z, stair("dark_oak", "south"))
        # outside stair at the west end up to the gallery
        for x, z in cells(1, 3, 2, z1):
            d.set(x, 6, z, "spruce_planks")
        for y in range(2, 6):
            d.set(1, y, 3, log("spruce_log", "y"))
        flight(d, 1, 11, 2, 5, "north", "spruce")
        d.set(1, 7, 3, fence("spruce"))
        d.set(2, 7, 3, fence("spruce"))
    else:
        for x in range(x1 - 1, x2 + 2):
            for z in (2, 3, 4, 5):
                d.set(x, top, z, stair("dark_oak", "south"))
    for k in range(B):
        d.set(x1 + 2 + 8 * k, top - 1 if F == 1 else 5, 4, lantern(True))
        if F == 2:
            d.set(x1 + 2 + 8 * k, 10, 4, lantern(True)) if top > 10 else None
    d.chair(x1 + 1, 2, 4, "north", "spruce", sit=False)
    d.chair(x1 + 2, 2, 4, "north", "spruce", sit=False)
    d.hut(x1 + 1 + 4, 2, z2 - 1)
    if L >= 5:
        d.item(x1 + 1 + 3, 2, z2 - 1, "ender_chest", "north")
    # yard: woodpile and a rail fence at the back
    for x in range(x1, x2 + 1):
        d.set(x, 2, 17, fence("spruce"))
    for x in range(x1 + 2, x1 + 6):
        d.set(x, 2, 16, log("spruce_log", "x"))
    d.set(x1 + 3, 3, 16, log("spruce_log", "x"))
    return d




# ============================================================================================ QUADPLEX
def quadplex_hw(rel, L, U=None, v=0):
    d = Design("Hearthwood", rel, (29, 22, 21), paving="grass_block[snowy=false]")
    U = U or min(L, 4)
    x0, z1, z2 = 3, 6, 15
    xe = x0 + 6 * U
    fills = ["calcite", "smooth_sandstone", "calcite", "white_terracotta"]
    W = "dark_oak"
    # ground storey brick, upper storey framed plaster (each house its own colour)
    brick_walls(d, x0, z1, xe, z2, 2, 4, "bricks", "stone_bricks")
    d.fill(x0, 5, z1, xe, 5, z2, "dark_oak_planks")
    for k in range(U):
        a = x0 + 6 * k
        hw_walls(d, a, z1, a + 6, z2, 6, 8, fills[k], "dark_oak_log", 2)
    d.clear(x0 + 1, 2, z1 + 1, xe - 1, 4, z2 - 1)
    d.clear(x0 + 1, 6, z1 + 1, xe - 1, 8, z2 - 1)
    d.fill(x0 + 1, 1, z1 + 1, xe - 1, 1, z2 - 1, "oak_planks")
    ridge = d.gable(x0, z1, xe, z2, 9, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite")
    for x in (x0, xe):
        for y in range(9, ridge):
            if d.get(x, y, 10) == "minecraft:calcite":
                d.set(x, y, 10, log("dark_oak_log", "y"))
    for k in range(U):
        a = x0 + 6 * k + 1                                 # interior a..a+4
        if k:
            d.fill(a - 1, 2, z1 + 1, a - 1, 8, z2 - 1, "bricks")
            d.fill(a - 1, 5, z1, a - 1, 5, z2, "dark_oak_planks")
        d.door(a + 1, 2, z1, "south", W)
        d.set(a + 1, 4, z1, log("dark_oak_log", "x"))
        hw_window(d, a + 3, 3, z1, 1)
        hw_window(d, a + 2, 3, z2, 1)
        for x in (a + 1, a + 3):
            hw_window(d, x, 7, z1, 1, "north")
        hw_window(d, a + 2, 7, z2, 1)
        # chimney breast on the west wall, stack through the roof
        d.hearth(a, 2, 9, "east", ridge + 2, "bricks", "campfire")
        alt = (k + v) % 3
        if alt == 0:    # two armchairs at the hearth
            d.chair(a + 2, 2, 8, "east", W)
            d.chair(a + 2, 2, 10, "east", W)
            d.set(a + 1, 2, 9, "red_carpet")
        elif alt == 1:  # a settle facing the hearth
            sofa(d, a + 2, 8, 2, 3, "south", "east", W, arms=False)
            d.set(a + 1, 2, 9, "green_carpet")
        else:           # rocking chair, side table with a lamp, books
            d.chair(a + 2, 2, 8, "east", W)
            d.chair(a + 2, 2, 10, "east", "spruce")
            fit(d, [(a + 3, 2, 8, "bookshelf"), (a + 1, 2, 9, "blue_carpet"), (a + 3, 2, 10, slab(W, "top")),
                    (a + 3, 3, 10, LANTF)])
        # kitchen & table
        kitchen(d, [(a, 14, "furnace"), (a + 1, 14, "sink"), (a + 2, 14, "smoker"), (a + 3, 14, "crafting_table")],
                2, "north", W)
        d.item(a, 2, 13, "barrel", "east")
        d.item(a, 2, 12, "barrel", "east")
        d.table(a + 2, 2, 12, W)
        d.chair(a + 1, 2, 12, "west", W)
        d.chair(a + 3, 2, 12, "east", W)
        d.lamp(a + 2, 4, 11)
        # stair along the east wall
        flight(d, a + 4, 9, 2, 4, "south", W, support="dark_oak_planks")
        for z in range(10, 13):
            d.set(a + 3, 6, z, fence(W))
        # bedroom
        bedset(d, a + 1, 6, z1 + 1, "north", ("l",) if not (k == 0 and L >= 5) else (), ("red", "blue", "green",
                                                                                       "yellow")[k], W)
        if k == 0 and L >= 5:
            d.bed(a + 2, 6, z1 + 1, "north", "red")
        nightstand(d, a + 3 if not (k == 0 and L >= 5) else a + 3, 6, z1 + 1, W, "candle")
        wardrobe(d, a, 6, 13, "east", W)
        d.lamp(a + 2, 8, 10)
        rugc(d, a + 1, 9, a + 2, 11, 6, "light_gray")
        # front garden
        fl = (("poppy", "oxeye_daisy", "rose_bush[half=lower]"), ("cornflower", "allium", "peony[half=lower]"),
              ("dandelion", "azure_bluet", "lilac[half=lower]"), ("red_tulip", "white_tulip", "rose_bush[half=lower]"))[k]
        garden(d, a - 1, 1, a + 5, z1 - 2, 2, "spruce", ((a + 1, 1, "north"),),
               plants=((a, 2, fl[0]), (a + 3, 2, fl[1]), (a + 4, 3, fl[2])))
        for z in range(0, z1):
            d.set(a + 1, 1, z, "gravel")
        clear_above_path(d, [(a + 1, z) for z in range(0, z1)], 1)
        for z in range(2, z1 - 2):
            d.set(a + 1, 2, z, AIR)
        d.set(a + 1, 2, z1 - 2, gate("spruce", "north"))
    d.hut(x0 + 4, 2, z1 + 1)
    if L >= 5:
        d.item(x0 + 1, 2, z1 + 1, "jukebox")
        d.item(x0 + 7 + 3, 2, z1 + 1, "ender_chest", "south")
    return d


def cabin(d, x1, z1, out, mirror, Y, bedc, extra_barrel=True, double=False, porch=True, layout=None):
    """Small log cabin around a 7x6 studio: outer x1..x1+8, z1..z1+7. `out` = window side (north/south);
    the door faces the other way onto a little porch."""
    x2, z2 = x1 + 8, z1 + 7
    log_walls(d, x1, z1, x2, z2, Y, Y + 3, "stripped_spruce_log", "spruce_log")
    d.fill(x1 + 1, Y - 1, z1 + 1, x2 - 1, Y - 1, z2 - 1, "spruce_planks")
    d.clear(x1 + 1, Y, z1 + 1, x2 - 1, Y + 3, z2 - 1)
    for x in range(x1, x2 + 1):
        for z in (z1, z2):
            d.set(x, Y + 3, z, log("spruce_log", "x"))
    ridge = d.gable(x1, z1, x2, z2, Y + 4, "x", "dark_oak_stairs", "dark_oak_slab", log("stripped_spruce_log", "z"))
    if out == "north":
        ox, oz = (x1 + 1, z1 + 1) if not mirror else (x2 - 1, z1 + 1)
        dz_door, porch_z = z2, (z2 + 1, z2 + 2)
    else:
        ox, oz = (x1 + 1, z2 - 1) if mirror else (x2 - 1, z2 - 1)
        dz_door, porch_z = z1, (z1 - 2, z1 - 1)
    Wf = flat(d, ox, oz, Y, out, mirror, layout or CABINS[0], "spruce", None, bedc, Y + 3, double=double)
    dx, dz = Wf(4, 6)
    d.door(dx, Y, dz, OPP[out], "spruce")
    for lx in (1, 2):
        x, z = Wf(lx, 6)
        ca_window(d, x, Y + 1, z, OPP[out], 1, shutters=False)
    for lx in (3, 5):
        x, z = Wf(lx, -1)
        ca_window(d, x, Y + 1, z, out, 2, shutters=lx == 3)
    x, z = Wf(-1, 2)
    ca_window(d, x, Y + 1, z, D4 and (OPP[CW[out]] if not mirror else CW[out]), 1, shutters=False)
    # stone chimney at the kitchen end
    cx, cz = Wf(7, 2)
    ex, ez = cx - Wf(6, 2)[0], cz - Wf(6, 2)[1]
    for y in range(Y - 1, ridge + 2):
        d.set(cx + ex, y, cz + ez, "cobblestone" if y % 3 else "mossy_cobblestone")
    if porch:
        for z in porch_z:
            for x in range(x1, x2 + 1):
                d.set(x, Y - 1, z, "spruce_planks")
        pz = porch_z[1] if out == "north" else porch_z[0]
        for x in (x1, x2):
            for y in range(Y, Y + 3):
                d.set(x, y, pz, log("spruce_log", "y"))
        for x in range(x1 - 1, x2 + 2):
            for z in porch_z:
                d.set(x, Y + 3, z, stair("spruce", out))
        for x in range(x1 + 1, x2):
            if abs(x - dx) > 1:
                d.set(x, Y, pz, fence("spruce"))
        d.set(dx + 2 if dx + 2 < x2 else dx - 2, Y, porch_z[0] if out == "north" else porch_z[1],
              stair("spruce", out))
    return Wf



def quadplex_nt(rel, L, U=None, v=0):
    d = Design("Neoterra", rel, (31, 20, 19), paving="smooth_stone")
    U = U or min(L, 4)
    W = "birch"
    for k in range(U):
        a = 3 + 7 * k                                       # interior a..a+4
        b = 4 if k % 2 == 0 else 6                          # front wall z (staggered)
        x1, x2, z1, z2 = a - 1, a + 5, b, b + 10
        nt_box(d, x1, z1, x2, z2, 2, 4, "white_concrete" if k % 2 == 0 else "light_gray_concrete", "white_concrete")
        nt_box(d, x1, z1, x2, z2, 6, 8, "white_concrete", "white_concrete")
        d.fill(x1, 5, z1, x2, 5, z2, "cyan_terracotta" if k % 2 == 0 else "smooth_quartz")
        d.fill(a, 1, z1 + 1, a + 4, 1, z2 - 1, "polished_diorite")
        d.fill(a, 5, z1 + 1, a + 4, 5, z2 - 1, "birch_planks")
        d.clear(a, 2, z1 + 1, a + 4, 4, z2 - 1)
        d.clear(a, 6, z1 + 1, a + 4, 8, z2 - 1)
        d.flat(x1, z1, x2, z2, 9, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
        for x, z in cells(a, z1 + 6, a + 4, z2 - 1):        # green roof at the back
            d.set(x, 10, z, "moss_block")
            if (x + z) % 3 == 0:
                d.set(x, 11, z, "azalea")
        # glass front: full height ground, ribbon upstairs; side door
        for x in range(a, a + 5):
            d.window(x, 2, z1, x, 4, z1)
            d.window(x, 6, z1, x, 8, z1, "light_gray_stained_glass_pane" if x == a + 4 else "glass_pane")
        d.door(a + 4, 2, z1, "south", W)
        d.window(a + 1, 3, z2, a + 2, 4, z2)
        d.set(a + 4, 4, z1 - 1, slab("smooth_quartz", "top"))
        d.set(a + 3, 4, z1 - 1, slab("smooth_quartz", "top"))
        # ground: sofa facing the street glass, dining, kitchen along the back wall
        alt = (k + v) % 3
        if alt == 0:    # sofa facing the street glass
            sofa(d, a, z1 + 3, 2, 2, "east", "south", W, arms=False)
            d.set(a, 2, z1 + 1, "potted_bamboo")
            rugc(d, a, z1 + 2, a + 2, z1 + 2, 2, "cyan")
        elif alt == 1:  # two lounge chairs either side of a low table
            d.chair(a, 2, z1 + 2, "west", W)
            d.chair(a + 2, 2, z1 + 2, "east", W)
            fit(d, [(a + 1, 2, z1 + 2, slab("smooth_quartz")), (a, 2, z1 + 1, "potted_fern")])
            rugc(d, a, z1 + 3, a + 2, z1 + 3, 2, "orange")
        else:           # work-from-home corner: desk on the glass, chair, plant
            d.chair(a, 2, z1 + 2, "south", W)
            fit(d, [(a, 2, z1 + 1, slab("smooth_quartz", "top")), (a + 1, 2, z1 + 1, slab("smooth_quartz", "top")),
                    (a + 2, 2, z1 + 1, "potted_bamboo")])
            rugc(d, a, z1 + 3, a + 2, z1 + 3, 2, "lime")
        d.table(a + 1, 2, z1 + 6, W, "slab", "smooth_quartz_slab")
        d.chair(a, 2, z1 + 6, "west", W)
        d.chair(a + 2, 2, z1 + 6, "east", W)
        kitchen(d, [(a, z2 - 1, "furnace"), (a + 1, z2 - 1, "sink"), (a + 2, z2 - 1, "smoker"),
                    (a + 3, z2 - 1, "crafting_table")], 2, "north", W, top="smooth_quartz")
        d.item(a + 4, 2, z2 - 1, "barrel", "north")
        d.item(a + 4, 2, z2 - 2, "barrel", "west")
        d.set(a + 1, 5, z1 + 4, "sea_lantern")
        # stair along the east wall
        flight(d, a + 4, z1 + 3, 2, 4, "south", "smooth_quartz")
        for z in range(z1 + 4, z1 + 7):
            d.set(a + 3, 6, z, "glass_pane")
        # bedroom upstairs
        dbl = k == 0 and L >= 5
        d.bed(a + 1, 6, z1 + 1, "north", ("cyan", "lime", "light_blue", "magenta")[k])
        if dbl:
            d.bed(a + 2, 6, z1 + 1, "north", "cyan")
        nightstand(d, a, 6, z1 + 1, W, "end_rod[facing=up]")
        nightstand(d, a + 3 if dbl else a + 2, 6, z1 + 1, W, "end_rod[facing=up]")
        wardrobe(d, a, 6, z2 - 1, "east", W)
        d.set(a + 1, 6, z2 - 1, slab("smooth_quartz", "top"))
        d.chair(a + 1, 6, z2 - 2, "south", W, sit=False)
        d.set(a + 2, 9, z1 + 4, "sea_lantern")
        # front planter + walk
        planter(d, a, z1 - 2, a + 2, z1 - 2, 1)
        for z in range(0, z1):
            d.set(a + 4, 1, z, "polished_andesite")
    d.hut(3, 2, 5)
    if L >= 5:
        d.item(4, 6, 13, "jukebox")
        d.item(5, 6, 13, "ender_chest", "west")
    return d




# ============================================================================================ PLAYER HOUSE
def barrel_lines(d, cols, y, n, h=3):
    """Storage shelving: barrels stacked h high in the given columns [(x, z, facing)] until n are placed."""
    placed = 0
    for x, z, f in cols:
        for k in range(h):
            if placed >= n:
                return placed
            d.item(x, y + k, z, "barrel", f)
            placed += 1
    return placed


def items(d, seq, y, facing):
    for x, z, k in seq:
        if k is None:
            continue
        if k == "water_cauldron":
            d.item(x, y, z, "water_cauldron[level=3]")
        elif k == "composter":
            d.item(x, y, z, "composter[level=0]")
        elif k in ("cartography_table", "fletching_table", "smithing_table", "crafting_table", "enchanting_table",
                   "jukebox"):
            d.item(x, y, z, k)
        else:
            d.item(x, y, z, k, facing)


def bookcases(d, cols, y, n, h=3):
    placed = 0
    for x, z in cols:
        for k in range(h):
            if placed >= n:
                return placed
            d.bookshelf(x, y + k, z)
            placed += 1
    return placed


def ph_req(rel):
    from hm import REQ
    return REQ[rel]


def playerhouse_hw(rel, L):
    d = Design("Hearthwood", rel, (31, 24, 30), paving="grass_block[snowy=false]")
    W = "dark_oak"
    R = ph_req(rel)
    nb = R["items"].get("minecraft:barrel", 0)
    x1, x2, z1, z2 = 3, 19, 3, 12
    y0, deck, yu, top = 2, 6, 7, 9
    # ---- manor: brick ground storey, close-studded upper storey, steep tiled roof, two chimneys
    brick_walls(d, x1, z1, x2, z2, y0, deck - 1, "bricks", "stone_bricks", "stone_bricks")
    d.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, z2 - 1, "oak_planks")
    d.clear(x1 + 1, y0, z1 + 1, x2 - 1, deck - 1, z2 - 1)
    d.fill(x1, deck, z1, x2, deck, z2, "dark_oak_planks")
    hw_walls(d, x1, z1, x2, z2, yu, top, "calcite", "dark_oak_log", 2)
    d.clear(x1 + 1, yu, z1 + 1, x2 - 1, top, z2 - 1)
    ridge = d.gable(x1, z1, x2, z2, top + 1, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite")
    # front cross-gable porch bay over the door
    for x in range(10, 15):
        for y in range(y0, deck):
            d.set(x, y, z1 - 2, "stone_bricks" if x in (10, 14) else AIR)
    for x in (10, 14):
        d.set(x, y0, z1 - 1, "stone_bricks")
        for y in range(y0, deck):
            d.set(x, y, z1 - 1, "stone_bricks")
    d.fill(10, deck, z1 - 2, 14, deck, z1 - 1, "dark_oak_planks")
    hw_walls(d, 10, z1 - 2, 14, z1, yu, top, "calcite", "dark_oak_log", 2)
    d.clear(11, yu, z1 - 1, 13, top, z1)
    d.gable(10, z1 - 2, 14, z1 + 1, top + 1, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite")
    for x in (11, 13):
        hw_window(d, x, 8, z1 - 2, 1)
    d.set(12, 8, z1 - 2, "glass_pane")
    d.set(12, 9, z1 - 2, "glass_pane")
    d.door(12, y0, z1, "south", W)
    d.set(12, y0 + 2, z1, "stone_bricks")
    for y in (y0, y0 + 1):
        d.set(11, y, z1 - 2, "stone_brick_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
        d.set(13, y, z1 - 2, "stone_brick_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
    d.set(11, y0 + 2, z1 - 2, stair("stone_brick", "west", "top"))
    d.set(13, y0 + 2, z1 - 2, stair("stone_brick", "east", "top"))
    d.set(12, y0 + 3, z1 - 2, "stone_bricks")
    d.set(12, y0 + 2, z1 - 1, lantern(True))
    sofa(d, 11, z1 - 1, yu, 3, "east", "north", W, arms=False, sit=False)      # window seat in the bay
    # windows
    for x in (5, 6, 8, 16, 17):
        hw_window(d, x, 3, z1, 2)
    for x in (5, 7, 16, 18):
        hw_window(d, x, 8, z1, 1, "north")
    for x in (5, 7, 15, 17):
        hw_window(d, x, 3, z2, 2)
        hw_window(d, x, 8, z2, 1)
    for z in (5, 9):
        hw_window(d, x1, 8, z, 1)
        hw_window(d, x2, 8, z, 1)
        hw_window(d, x2, 3, z, 2) if z == 9 else None
    # ---- ground: hall with inglenook, dining, kitchen, pantry
    fireplace(d, x1, 6, y0, "east", ridge + 2, "bricks", "bricks")
    d.chair(5, y0, 5, "west", W, arms=False)
    d.chair(5, y0, 7, "west", W, arms=False)
    rugc(d, 4, 5, 4, 7, y0, "red")
    for x in (6, 7, 8):
        d.table(x, y0, 10, W)
        d.chair(x, y0, 9, "north", W)
    d.chair(5, y0, 10, "west", W)
    d.chair(9, y0, 10, "east", W)
    for x in (6, 7, 8):
        d.chair(x, y0, 11, "south", W)
    d.lamp(7, 5, 10)
    d.lamp(5, 5, 6)
    d.hut(4, y0, 4)
    if L >= 4:
        d.item(4, y0, 11, "jukebox")
    # stair in the hall, rising south
    flight(d, 12, 5, y0, 5, "south", W, support=None)
    for z in range(6, 9):
        d.set(11, yu, z, fence(W))
        d.set(13, yu, z, fence(W))
    # kitchen along the back wall + pantry (east, behind a partition)
    k2 = L >= 2
    kitchen(d, [(13, 11, "furnace"), (14, 11, "furnace"), (15, 11, "sink"),
                (16, 11, "smoker" if k2 else "counter"), (17, 11, "smoker" if k2 else "counter"),
                (18, 11, "crafting_table")], y0, "north", W)
    d.item(18, y0, 10, "crafting_table")
    d.lamp(15, 5, 9)
    partition(d, 14, 9, 18, 9, y0, 5, "spruce_planks", ((15, 9, "north"),), "spruce")
    d.fill(14, y0, 4, 14, 5, 8, "spruce_planks")
    pantry = [(x, 4, "south") for x in (15, 16, 17)] + [(18, z, "west") for z in (5, 6, 7, 8)]
    left = max(0, (19 if L == 1 else 19) - 0)
    barrel_lines(d, pantry, y0, 19)
    d.lamp(16, 5, 6)
    # ---- upper: master bedroom (west), study / library (east)
    partition(d, 10, 4, 10, 11, yu, top, "calcite", ((10, 10, "east"),), W)
    partition(d, 14, 4, 14, 11, yu, top, "calcite", ((14, 10, "west"),), W)
    bedset(d, 4, yu, 6, "west", ("l",), "red", W)
    if L >= 3:
        d.bed(4, yu, 7, "west", "red")
        nightstand(d, 4, yu, 8, W, "candle")
    else:
        nightstand(d, 4, yu, 7, W, "candle")
    wardrobe(d, 9, yu, 4, "south", W)
    wardrobe(d, 8, yu, 4, "south", W)
    rugc(d, 6, 6, 8, 8, yu, "red")
    d.lamp(7, top, 7)
    d.set(4, yu, 11, "chest[facing=east,type=single,waterlogged=false]")
    if L >= 3:
        # library: bookcases floor to ceiling, enchanting table, lecterns, brewing corner
        cols = [(x, 4) for x in range(15, 19)] + [(18, z) for z in range(5, 9)] + [(x, 11) for x in range(15, 19)]
        bookcases(d, cols, yu, 35)
        d.item(16, yu, 6, "enchanting_table")
        rugc(d, 15, 5, 17, 7, yu, "purple")
        d.item(15, yu, 8, "lectern", "south")
        d.item(17, yu, 8, "lectern", "south")
        items(d, [(18, 9, "brewing_stand"), (18, 10, "brewing_stand"), (17, 10, "water_cauldron")], yu, "west")
        d.lamp(16, top, 9)
    else:
        if L >= 2:
            d.item(18, yu, 6, "lectern", "west")
        d.set(16, yu, 5, slab(W, "top"))
        d.chair(16, yu, 6, "south", W, sit=False)
        d.set(18, yu, 4, "bookshelf")
        d.lamp(16, top, 8)
    # ---- L2 tithe barn (storage aisles) and smithy; garden
    if L >= 2:
        d.door(10, y0, z2, "south", W)
        bx1, bx2, bz1, bz2 = 3, 17, 15, 27
        brick_walls(d, bx1, bz1, bx2, bz2, y0, 2, "stone_bricks", None)
        hw_walls(d, bx1, bz1, bx2, bz2, 3, 6, "oak_planks", "dark_oak_log", 3)
        d.fill(bx1 + 1, 1, bz1 + 1, bx2 - 1, 1, bz2 - 1, "stone_bricks")
        d.clear(bx1 + 1, y0, bz1 + 1, bx2 - 1, 6, bz2 - 1)
        d.gable(bx1, bz1, bx2, bz2, 7, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "oak_planks")
        for xx in (9, 10, 11):
            for y in range(y0, 6):
                d.set(xx, y, bz1, AIR)
        d.double_door(9, y0, bz1, "x", "south", "spruce")
        d.set(11, y0, bz1, "stone_bricks")
        for y in (3, 4, 5):
            d.set(11, y, bz1, "oak_planks")
        d.fill(9, 4, bz1, 11, 5, bz1, "oak_planks")
        d.fill(9, 4, bz1, 10, 4, bz1, log("dark_oak_log", "x"))
        cols = [(4, z, "east") for z in range(17, 26)] + [(16, z, "west") for z in range(17, 26)] \
            + [(x, 26, "north") for x in range(5, 16)] \
            + [(x, 19, "north") for x in range(7, 14)] + [(x, 20, "south") for x in range(7, 14)] \
            + [(x, 23, "north") for x in range(7, 14)] + [(x, 24, "south") for x in range(7, 14)]
        barrel_lines(d, cols, y0, nb - 19)
        for x in (6, 10, 14):
            d.set(x, 6, 21, lantern(True))
        for z in (18, 22):
            hw_window(d, bx1, 4, z, 1)
            hw_window(d, bx2, 4, z, 1)
        if L >= 4:
            d.item(15, y0, 16, "ender_chest", "west")
        # smithy: open-fronted forge shed with a brick forge chimney
        sx1, sx2, sz1, sz2 = 20, 28, 15, 24
        for x, z in cells(sx1, sz1, sx2, sz2):
            d.set(x, 1, z, "cobblestone" if (x + z) % 3 else "gravel")
        brick_walls(d, sx1, sz2, sx2, sz2, y0, 5, "bricks", "stone_bricks")
        brick_walls(d, sx2, sz1, sx2, sz2, y0, 5, "bricks", "stone_bricks")
        for x, z in ((sx1, sz1), (sx1, 19), (24, sz1)):
            for y in range(y0, 6):
                d.set(x, y, z, log("dark_oak_log", "y"))
        d.gable(sx1, sz1, sx2, sz2, 6, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "bricks")
        for z in range(sz1, sz2):
            if d.air(sx1, 5, z):
                d.set(sx1, 5, z, log("dark_oak_log", "z"))
        for x in range(sx1, sx2):
            if d.air(x, 5, sz1):
                d.set(x, 5, sz1, log("dark_oak_log", "x"))
        # forge: blast furnaces either side of a fire pit, chimney through the roof
        d.set(24, 1, 23, "bricks")
        d.set(24, y0, 23, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        for y in range(y0 + 1, 14):
            d.set(24, y, 23, "bricks")
        work = [(21, 23, "furnace"), (22, 23, "blast_furnace"), (23, 23, "blast_furnace"), (25, 23, "furnace"),
                (26, 23, "smithing_table"), (27, 23, "stonecutter"), (27, 22, "grindstone" if L >= 3 else None),
                (27, 21, "fletching_table"), (27, 20, "loom"), (27, 19, "cartography_table")]
        items(d, work, y0, "north")
        d.item(23, y0, 20, "anvil", "east")
        if L >= 3:
            d.item(25, y0, 20, "anvil", "east")
        d.set(27, y0, 17, "water_cauldron[level=3]")
        d.set(24, 5, 20, lantern(True))
        # kitchen garden with composter and a bench
        garden(d, 20, 26, 29, 28, y0, "spruce", ((20, 27, "west"),), beds=False)
        for x in range(21, 29):
            d.set(x, 1, 27, "farmland[moisture=7]")
            d.set(x, y0, 27, ("carrots[age=7]", "potatoes[age=7]", "wheat[age=7]")[x % 3])
        d.item(19, y0, 26, "composter")
        d.set(19, 1, 26, "grass_block[snowy=false]")
    # front lawn with a bench, and a back terrace with garden table (L5)
    for x in range(1, 30):
        if abs(x - 12) > 1:
            d.set(x, y0, 0, fence("spruce"))
    for z in range(0, z1 - 2):
        d.set(12, 1, z, "gravel")
    if L >= 5:
        for x, z in cells(20, 4, 28, 11):
            d.set(x, 1, z, "stone_bricks" if (x + z) % 2 else "polished_andesite")
        d.dining(23, y0, 7, 2, "x", "spruce", ("n", "s"))
        d.set(21, y0, 4, "flowering_azalea")
        d.set(27, y0, 10, "flowering_azalea")
    return d


def bookcases_fit(d, cols, y, n, hmax=3):
    """Bookcases in columns, each as tall as the free space allows (up to hmax)."""
    placed = 0
    for x, z in cols:
        for k in range(hmax):
            if placed >= n or not d.air(x, y + k, z):
                break
            d.bookshelf(x, y + k, z)
            placed += 1
    return placed


def playerhouse_ca(rel, L):
    d = Design("Cascadia", rel, (31, 22, 31), paving="grass_block[snowy=false]")
    W = "spruce"
    R = ph_req(rel)
    nb = R["items"].get("minecraft:barrel", 0)
    x1, x2, z1, z2 = 2, 14, 4, 13
    y0 = 2
    # ---- lodge: log walls on river rock, gable along x, deep porch, stone chimney
    log_walls(d, x1, z1, x2, z2, y0, 6, "stripped_spruce_log", "spruce_log")
    d.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, z2 - 1, "spruce_planks")
    d.clear(x1 + 1, y0, z1 + 1, x2 - 1, 6, z2 - 1)
    d.fill(x1 + 1, 6, z1 + 1, x2 - 1, 6, z2 - 1, "spruce_planks")
    for x in range(x1, x2 + 1):
        for z in (z1, z2):
            d.set(x, 6, z, log("spruce_log", "x"))
    ridge = d.gable(x1, z1, x2, z2, 7, "x", "dark_oak_stairs", "dark_oak_slab", log("stripped_spruce_log", "z"))
    d.window(x1, 9, 8, x1, 10, 9)
    d.window(x2, 9, 8, x2, 10, 9)
    d.door(8, y0, z1, "south", W)
    for x in (4, 6, 10, 12):
        ca_window(d, x, 3, z1, "north", 2)
    for x in (5, 11):
        ca_window(d, x, 3, z2, "south", 2) if x != 9 else None
    ca_window(d, x2, 3, 11, "east", 2)
    # porch
    for x, z in cells(x1, 1, x2, z1 - 1):
        d.set(x, 1, z, "spruce_planks")
    for x in (x1, 5, 11, x2):
        for y in range(y0, 5):
            d.set(x, y, 1, log("spruce_log", "y"))
    for x in range(x1 - 1, x2 + 2):
        d.set(x, 5, 0, stair("dark_oak", "south"))
        d.set(x, 5, 1, stair("dark_oak", "south"))
        d.set(x, 6, 2, stair("dark_oak", "south"))
        d.set(x, 6, 3, stair("dark_oak", "south"))
    for x in range(x1 + 1, x2):
        if abs(x - 8) > 1 and x not in (5, 11):
            d.set(x, y0, 1, fence(W))
    d.set(8, 4, 2, lantern(True))
    d.chair(3, y0, 3, "south", W, sit=L >= 3)
    d.chair(4, y0, 3, "south", W, sit=L >= 3)
    d.chair(12, y0, 3, "south", W, sit=L >= 5)
    d.chair(13, y0, 3, "south", W, sit=L >= 5)
    # ---- ground: hearth, dining, kitchen, stair, bed alcove
    fireplace(d, x1, 7, y0, "east", ridge + 2, "cobblestone", "mossy_cobblestone")
    for y in range(y0 + 2, ridge + 2):
        d.set(x1 - 1, y, 7, "cobblestone" if y % 3 else "mossy_cobblestone")
    d.chair(4, y0, 6, "west", W, arms=False)
    d.chair(4, y0, 8, "west", W, arms=False)
    rugc(d, 3, 6, 3, 8, y0, "brown")
    for x in (6, 7, 8):
        d.table(x, y0, 7, W)
        d.chair(x, y0, 6, "north", W)
        d.chair(x, y0, 8, "south", W)
    d.lamp(7, 5, 7)
    d.hut(3, y0, 5)
    k2 = L >= 2
    kitchen(d, [(13, 5, "furnace"), (13, 6, "furnace"), (13, 7, "sink"), (13, 8, "smoker" if k2 else "counter"),
                (13, 9, "smoker" if k2 else "counter")], y0, "west", W)
    d.item(11, y0, 5, "crafting_table")
    d.item(12, y0, 5, "crafting_table")
    flight(d, 7, 10, y0, 5, "east", W, support="spruce_planks")
    bedset(d, 13, y0, 12, "east", (), "brown", W)
    if L >= 3:
        d.bed(13, y0, 11, "east", "brown")
    nightstand(d, 11, y0, 12, W, "lantern")
    wardrobe(d, 3, y0, 12, "east", W)
    if L >= 4:
        d.item(3, y0, 10, "jukebox")
    d.lamp(10, 5, 12)
    # loft: study / library under the roof
    for x in (8, 9, 10):
        d.set(x, 7, 9, fence(W))
        d.set(x, 7, 11, fence(W))
    d.set(8, 10, 7, lantern(True))
    if L >= 3:
        cols = [(3, z) for z in range(5, 13)] + [(13, z) for z in range(5, 10)] + [(x, 12) for x in range(4, 7)] \
            + [(x, 5) for x in range(4, 8)] + [(x, 5) for x in range(9, 13)]
        bookcases_fit(d, cols, 7, 35)
        d.item(8, 7, 7, "enchanting_table")
        rugc(d, 7, 6, 9, 8, 7, "green")
        d.item(6, 7, 7, "lectern", "east")
        d.item(10, 7, 7, "lectern", "west")
        items(d, [(4, 11, "brewing_stand"), (5, 11, "brewing_stand"), (6, 11, "water_cauldron")], 7, "north")
    else:
        if L >= 2:
            d.item(6, 7, 7, "lectern", "east")
        d.set(4, 7, 6, "chest[facing=east,type=single,waterlogged=false]")
        d.set(4, 7, 7, "chest[facing=east,type=single,waterlogged=false]")
    # ---- root-cellar lean-to at the back (pantry, 19 barrels)
    px1, px2, pz1, pz2 = x1, x2, z2, 17
    for x, z in cells(px1, pz1, px2, pz2):
        if x in (px1, px2) or z == pz2:
            for y in range(y0, 5):
                d.set(x, y, z, "cobblestone" if y == y0 else "spruce_planks")
    d.fill(px1 + 1, 1, pz1 + 1, px2 - 1, 1, pz2 - 1, "packed_mud")
    shed_roof(d, px1, pz1 + 1, px2, pz2, 5, "south", "spruce")
    for z in range(pz1 + 1, pz2):
        for y in range(5, 5 + (pz2 - z)):
            for x in (px1, px2):
                d.set(x, y, z, "spruce_planks")
    d.door(9, y0, z2, "south", W)
    barrel_lines(d, [(x, 16, "north") for x in range(3, 14)], y0, 19)
    d.set(8, 4, 15, lantern(True))
    # ---- L2 barn (storage) and workshop shed
    if L >= 2:
        bx1, bx2, bz1, bz2 = 17, 29, 5, 25
        for y in range(y0, 8):
            for x, z in cells(bx1, bz1, bx2, bz2):
                if x in (bx1, bx2) or z in (bz1, bz2):
                    d.set(x, y, z, "spruce_planks" if y > y0 else "cobblestone")
        for x, z in cells(bx1, bz1, bx2, bz2):
            if (x in (bx1, bx2) and (z - bz1) % 4 == 0) or (z in (bz1, bz2) and (x - bx1) % 4 == 0):
                for y in range(y0 + 1, 8):
                    d.set(x, y, z, log("spruce_log", "y"))
        d.fill(bx1 + 1, 1, bz1 + 1, bx2 - 1, 1, bz2 - 1, "spruce_planks")
        d.clear(bx1 + 1, y0, bz1 + 1, bx2 - 1, 7, bz2 - 1)
        ridge_b = d.gable(bx1, bz1, bx2, bz2, 8, "z", "spruce_stairs", "spruce_slab", "spruce_planks")
        for z in (bz1, bz2):                                     # hay door and loft beam on the gables
            d.window(23, 10, z, 23, 11, z, "glass_pane")
        for x in range(21, 26):
            for y in range(y0, 6):
                d.set(x, y, bz1, AIR)
        for x in (21, 25):
            for y in range(y0, 6):
                d.set(x, y, bz1, log("spruce_log", "y"))
        d.double_door(22, y0, bz1, "x", "south", W)
        d.door(24, y0, bz1, "south", W)
        for x in range(21, 26):
            d.set(x, 4, bz1, log("spruce_log", "x"))
            d.set(x, 5, bz1, "spruce_planks")
        for x in (22, 23, 24):                                  # X-braced barn door look above
            d.set(x, 6, bz1, log("stripped_spruce_log", "x"))
        cols = [(18, z, "east") for z in range(7, 25)] + [(28, z, "west") for z in range(7, 25)] \
            + [(x, 24, "north") for x in range(19, 28)]
        barrel_lines(d, cols, y0, nb - 19)
        for z in (9, 15, 21):
            d.set(23, 7, z, lantern(True))
        for z in (12, 18):
            ca_window(d, bx2, 5, z, "east", 1, shutters=False)
        if L >= 4:
            d.item(20, y0, 6, "ender_chest", "south")
        # hay bales in the loft corners
        # workshop shed behind the lodge: open to the yard (north), stone forge chimney
        wx1, wx2, wz1, wz2 = 2, 14, 21, 28
        for x, z in cells(wx1, wz1, wx2, wz2):
            d.set(x, 1, z, "packed_mud" if (x + z) % 3 else "coarse_dirt")
        for x in range(wx1, wx2 + 1):
            for y in range(y0, 6):
                d.set(x, y, wz2, log("stripped_spruce_log", "x") if y > y0 else "cobblestone")
        for z in range(wz1, wz2 + 1):
            for y in range(y0, 6):
                d.set(wx1, y, z, log("stripped_spruce_log", "z") if y > y0 else "cobblestone")
                d.set(wx2, y, z, log("stripped_spruce_log", "z") if y > y0 else "cobblestone")
        for x in (wx1, 6, 10, wx2):
            for y in range(y0, 6):
                d.set(x, y, wz1, log("spruce_log", "y"))
        d.gable(wx1, wz1, wx2, wz2, 6, "x", "dark_oak_stairs", "dark_oak_slab", log("stripped_spruce_log", "z"))
        d.set(8, 1, 27, "cobblestone")
        d.set(8, y0, 27, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        for y in range(y0 + 1, 13):
            d.set(8, y, 27, "cobblestone" if y % 3 else "mossy_cobblestone")
        work = [(4, 27, "furnace"), (5, 27, "furnace"), (6, 27, "blast_furnace"), (7, 27, "blast_furnace"),
                (9, 27, "smithing_table"), (10, 27, "stonecutter"), (11, 27, "grindstone" if L >= 3 else None),
                (13, 26, "fletching_table"), (13, 25, "loom"), (13, 24, "cartography_table")]
        items(d, work, y0, "north")
        d.item(7, y0, 24, "anvil", "east")
        if L >= 3:
            d.item(10, y0, 24, "anvil", "east")
        d.set(3, y0, 27, log("spruce_log", "y"))
        d.set(3, y0, 26, log("spruce_log", "y"))
        d.set(3, y0 + 1, 27, log("spruce_log", "y"))
        d.set(8, 5, 24, lantern(True))
        d.item(16, y0, 28, "composter")
        for x, z in cells(17, 27, 23, 29):
            d.set(x, 1, z, "farmland[moisture=7]")
            d.set(x, y0, z, ("carrots[age=7]", "potatoes[age=7]", "beetroots[age=3]")[x % 3])
    # yard: rail fence along the street, gravel track
    for x in range(0, 31):
        if x not in (7, 8, 9, 22, 23, 24):
            d.set(x, y0, 0, fence(W)) if not (x1 - 1 <= x <= x2 + 1) else None
    for z in range(0, 5):
        for x in (22, 23, 24):
            d.set(x, 1, z, "coarse_dirt" if (x + z) % 2 else "gravel")
    return d


def playerhouse_nt(rel, L):
    d = Design("Neoterra", rel, (29, 24, 31), paving="smooth_stone")
    W = "birch"
    R = ph_req(rel)
    nb = R["items"].get("minecraft:barrel", 0)
    x1, x2, z1, z2 = 2, 12, 3, 20
    y0 = 2
    # ---- villa: two white storeys, glass street end, cantilevered upper floor, flat roof
    nt_box(d, x1, z1, x2, z2, y0, 5)
    d.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, z2 - 1, "polished_diorite")
    d.clear(x1 + 1, y0, z1 + 1, x2 - 1, 5, z2 - 1)
    d.fill(x1, 6, z1 - 1, x2 + 1, 6, z2, "light_gray_concrete")
    nt_box(d, x1, z1 - 1, x2 + 1, z2, 7, 9)
    d.fill(x1 + 1, 6, z1, x2, 6, z2 - 1, "birch_planks")
    d.clear(x1 + 1, 7, z1, x2, 9, z2 - 1)
    d.flat(x1, z1 - 1, x2 + 1, z2, 10, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
    for x in range(x1, x2 + 2):
        d.set(x, 6, z1 - 1, "cyan_terracotta")
    for x in range(x1 + 1, x2):
        if x != 6:
            d.window(x, y0, z1, x, 5, z1)
        d.window(x, 7, z1 - 1, x, 9, z1 - 1)
    d.door(6, y0, z1, "south", W)
    d.set(6, 4, z1, "glass_pane")
    d.set(6, 5, z1, "glass_pane")
    for z in range(z1 + 1, z1 + 7):
        d.window(x1, 3, z, x1, 4, z)
    for z in range(z1 + 2, z2 - 1, 2):
        d.window(x1, 8, z, x1, 9, z)
    # ---- ground: living with a linear fire, dining, kitchen, pantry
    fireplace(d, x1, 7, y0, "east", 12, "polished_blackstone_bricks", fire="soul_campfire")
    d.chair(4, y0, 6, "west", W, arms=False)
    d.chair(4, y0, 8, "west", W, arms=False)
    rugc(d, 3, 6, 3, 8, y0, "light_gray")
    for x in (6, 7, 8):
        d.table(x, y0, 6, W, "slab", "smooth_quartz_slab")
        d.chair(x, y0, 5, "north", W)
        d.chair(x, y0, 7, "south", W)
    d.set(4, y0, 4, "potted_bamboo")
    d.set(4, y0, 10, "potted_bamboo")
    d.hut(11, y0, 4)
    for x, z in ((7, 6), (7, 12), (7, 17)):
        d.set(x, 5, z, "sea_lantern")
    k2 = L >= 2
    kitchen(d, [(11, 9, "furnace"), (11, 10, "furnace"), (11, 11, "sink"), (11, 12, "smoker" if k2 else "counter"),
                (11, 13, "smoker" if k2 else "counter"), (11, 14, "crafting_table")], y0, "west", W,
            top="smooth_quartz")
    d.item(11, y0, 15, "crafting_table")
    for z in (11, 12, 13):                                         # island
        d.set(8, y0, z, "smooth_quartz")
    if L >= 4:
        d.item(3, y0, 4, "jukebox")
    flight(d, 3, 10, y0, 5, "south", "smooth_quartz")
    # pantry behind a partition at the back
    partition(d, 3, 17, 11, 17, y0, 5, "white_concrete", ((8, 17, "north"),), W)
    barrel_lines(d, [(x, 19, "north") for x in range(3, 12)], y0, 19)
    d.set(7, 5, 18, "sea_lantern")
    # ---- upper: bedroom suite (front), study / library (back)
    for z in range(12, 15):
        d.set(4, 7, z, "glass_pane")
    partition(d, 3, 11, 11, 11, 7, 9, "white_concrete", ((6, 11, "north"),), W)
    d.set(4, 7, 11, "white_concrete")
    bedset(d, 3, 7, 6, "west", ("l",), "light_gray", W, light="end_rod[facing=up]")
    if L >= 3:
        d.bed(3, 7, 7, "west", "light_gray")
        nightstand(d, 3, 7, 8, W, "end_rod[facing=up]")
    else:
        nightstand(d, 3, 7, 7, W, "end_rod[facing=up]")
    wardrobe(d, 11, 7, 9, "west", W)
    wardrobe(d, 11, 7, 8, "west", W)
    d.set(11, 7, 5, slab("smooth_quartz", "top"))                              # dressing table
    d.set(11, 8, 5, "potted_azure_bluet")
    d.chair(10, 7, 5, "west", W, sit=False)
    rugc(d, 5, 5, 8, 8, 7, "cyan")
    d.set(7, 10, 7, "sea_lantern")
    if L >= 3:
        cols = [(x, 19) for x in range(5, 12)] + [(11, z) for z in range(15, 19)] + [(x, 12) for x in range(8, 12)]
        bookcases_fit(d, cols, 7, 35)
        d.item(7, 7, 16, "enchanting_table")
        rugc(d, 6, 15, 8, 17, 7, "purple")
        d.item(5, 7, 16, "lectern", "east")
        d.item(9, 7, 16, "lectern", "west")
        d.chair(6, 7, 13, "north", W)
        d.chair(7, 7, 13, "north", W)
        items(d, [(3, 19, "brewing_stand"), (4, 19, "brewing_stand"), (3, 18, "water_cauldron")], 7, "north")
        d.set(7, 10, 16, "sea_lantern")
    else:
        if L >= 2:
            d.item(9, 7, 16, "lectern", "west")
        d.set(7, 7, 19, slab("smooth_quartz", "top"))
        d.chair(7, 7, 18, "south", W, sit=False)
        d.set(5, 7, 19, "bookshelf")
        d.set(6, 7, 19, "bookshelf")
        sofa(d, 11, 13, 7, 3, "south", "east", W, arms=False, sit=False)
        d.set(9, 7, 14, slab("smooth_quartz", "top"))
        d.set(9, 8, 14, "potted_flowering_azalea_bush")
        d.set(11, 7, 17, "potted_bamboo")
    # ---- L2 workshop studio (NE) and storage hall (SE)
    if L >= 2:
        sx1, sx2, sz1, sz2 = 15, 27, 3, 10
        nt_box(d, sx1, sz1, sx2, sz2, y0, 5, "light_gray_concrete", "white_concrete")
        d.fill(sx1 + 1, 1, sz1 + 1, sx2 - 1, 1, sz2 - 1, "polished_andesite")
        d.clear(sx1 + 1, y0, sz1 + 1, sx2 - 1, 5, sz2 - 1)
        d.flat(sx1, sz1, sx2, sz2, 6, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
        for x in range(sx1 + 1, sx2):
            d.window(x, y0, sz1, x, 5, sz1)
        d.double_door(20, y0, sz1, "x", "south", W)
        work = [(16, 9, "furnace"), (17, 9, "furnace"), (18, 9, "blast_furnace"), (19, 9, "blast_furnace"),
                (21, 9, "smithing_table"), (22, 9, "stonecutter"), (23, 9, "grindstone" if L >= 3 else None),
                (26, 8, "fletching_table"), (26, 7, "loom"), (26, 6, "cartography_table")]
        items(d, work, y0, "north")
        d.item(20, y0, 6, "anvil", "east")
        if L >= 3:
            d.item(23, y0, 6, "anvil", "east")
        for x in (17, 21, 25):
            d.set(x, 5, 6, "sea_lantern")
        for x in range(sx1 + 2, sx2 - 1, 2):
            d.set(x, 7, 6, "daylight_detector[inverted=false,power=0]")
            d.set(x, 7, 7, "daylight_detector[inverted=false,power=0]")
        bx1, bx2, bz1, bz2 = 14, 27, 13, 28
        nt_box(d, bx1, bz1, bx2, bz2, y0, 6, "light_gray_concrete", "white_concrete")
        d.fill(bx1 + 1, 1, bz1 + 1, bx2 - 1, 1, bz2 - 1, "polished_andesite")
        d.clear(bx1 + 1, y0, bz1 + 1, bx2 - 1, 6, bz2 - 1)
        d.flat(bx1, bz1, bx2, bz2, 7, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
        for x in range(bx1 + 1, bx2):
            d.set(x, 6, bz1, "cyan_terracotta")
        for x in range(19, 23):
            for y in range(y0, 5):
                d.set(x, y, bz1, "light_gray_stained_glass_pane")
        d.double_door(20, y0, bz1, "x", "south", W)
        cols = [(15, z, "east") for z in range(15, 27)] + [(26, z, "west") for z in range(15, 27)] \
            + [(x, 27, "north") for x in range(16, 26)] + [(x, 20, "north") for x in range(19, 23)] \
            + [(x, 21, "south") for x in range(19, 23)]
        barrel_lines(d, cols, y0, nb - 19)
        for x, z in ((18, 18), (23, 18), (18, 24), (23, 24)):
            d.set(x, 6, z, "sea_lantern")
        for x in range(16, 26, 2):
            for z in range(15, 27, 3):
                d.set(x, 8, z, "daylight_detector[inverted=false,power=0]")
        if L >= 4:
            d.item(17, y0, 14, "ender_chest", "south")
        d.door(x2, y0, 16, "east", W)
        for x in range(x2 + 1, bx1):
            d.set(x, 1, 16, "smooth_stone")
        d.item(13, y0, 11, "composter")
        planter(d, 13, 8, 13, 10, 1)
    # ---- terrace (L5): table for four between the wings
    if L >= 5:
        for x, z in cells(3, 23, 12, 29):
            d.set(x, 1, z, "smooth_quartz" if (x + z) % 2 else "polished_diorite")
        d.dining(6, y0, 26, 2, "x", W, ("n", "s"))
        planter(d, 3, 29, 12, 29, 1)
        d.door(11, y0, z2, "south", W)
    return d




# ============================================================================================ composition
ROT_KEYS = ("north", "east", "south", "west")


def rot_state(s, k):
    """Rotate a block state by k quarter turns clockwise (seen from above)."""
    if k % 4 == 0:
        return s
    name, props = parse_state(s)
    if not props:
        return s
    new = dict(props)
    f = props.get("facing")
    if f in ROT_KEYS:
        for _ in range(k):
            f = CW[f]
        new["facing"] = f
    if "axis" in props and k % 2 == 1 and props["axis"] in ("x", "z"):
        new["axis"] = "z" if props["axis"] == "x" else "x"
    if any(key in props for key in ROT_KEYS):
        for key in ROT_KEYS:
            if key in props:
                t = key
                for _ in range(k):
                    t = CW[t]
                new[t] = props[key]
    if "rotation" in props:
        new["rotation"] = str((int(props["rotation"]) + 4 * k) % 16)
    return format_state(name, new)


def stamp(d, sub, dx, dz, rot=0, primary=False, crop=None, hut_to="chest"):
    """Copy the building drawn in Design `sub` into `d`: its ground layer only where it differs from its paving,
    everything above it, rotated k quarter turns clockwise, its (rotated) north-west corner at (dx, dz).
    primary=True also takes over the hut block and the requirement bookkeeping; other huts become `hut_to`."""
    sx, sz = sub.sx, sub.sz
    pave = sub.get(0, sub.gy, 0)
    hut = sub.req["hut"]

    def trf(x, z):
        w, h = sx, sz
        for _ in range(rot % 4):
            x, z = h - 1 - z, x
            w, h = h, w
        return x, z
    for x, y, z, st in sub.bp.blocks():
        if y < sub.gy or st == AIR:
            continue
        if crop and not (crop[0] <= x <= crop[2] and crop[1] <= z <= crop[3]):
            continue
        if y == sub.gy and st == pave:
            continue
        if "substitution" in st:
            continue
        rx, rz = trf(x, z)
        ty = y - sub.gy + d.gy
        te = sub.bp.tile_entities.get((x, y, z))
        if st.split("[")[0] == hut:
            if primary:
                d.set(dx + rx, ty, dz + rz, rot_state(st, rot))
                d.hut_pos = (dx + rx, ty, dz + rz)
            else:
                d.set(dx + rx, ty, dz + rz, hut_to if hut_to != "chest" else
                      f"chest[facing={rot_state('chest[facing=south]', rot).split('=')[1][:-1]},type=single,"
                      f"waterlogged=false]")
            continue
        d.set(dx + rx, ty, dz + rz, rot_state(st, rot), te)
    for (x, y, z), names in sub.tags.items():
        if crop and not (crop[0] <= x <= crop[2] and crop[1] <= z <= crop[3]):
            continue
        rx, rz = trf(x, z)
        d.tags.setdefault((dx + rx, y - sub.gy + d.gy, dz + rz), []).extend(names)
    if primary:
        P, Q = d.placed, sub.placed
        for k in ("beds", "racks", "floor_items", "seats", "bookshelves"):
            P[k] += Q[k]
        for k in ("items", "yard", "spots"):
            for kk, v in Q[k].items():
                P[k][kk] = P[k].get(kk, 0) + v
    return d


def tree(d, x, z, y, kind="oak", h=4, r=2):
    """Simple broadleaf / conifer tree with persistent leaves."""
    lv = f"{kind}_leaves[distance=1,persistent=true,waterlogged=false]"
    for k in range(h):
        d.set(x, y + k, z, log(f"{kind}_log", "y"))
    if kind == "spruce":
        for k, rr in ((h - 3, 2), (h - 2, 1), (h - 1, 2), (h, 1), (h + 1, 0)):
            for ax in range(-rr, rr + 1):
                for az in range(-rr, rr + 1):
                    if abs(ax) + abs(az) <= rr + (1 if rr == 2 else 0) and (ax or az or k >= h):
                        if d.bp.inside(x + ax, y + k, z + az) and d.air(x + ax, y + k, z + az):
                            d.set(x + ax, y + k, z + az, lv)
        return
    for k in range(h - 2, h + 2):
        rr = r if k < h + 1 else r - 1
        for ax in range(-rr, rr + 1):
            for az in range(-rr, rr + 1):
                if abs(ax) == rr and abs(az) == rr and (k + ax) % 2:
                    continue
                if d.bp.inside(x + ax, y + k, z + az) and d.air(x + ax, y + k, z + az):
                    d.set(x + ax, y + k, z + az, lv)


def lamp_post(d, x, z, y, kind="hw"):
    if kind == "nt":
        d.set(x, y, z, "smooth_quartz")
        for k in (1, 2):
            d.set(x, y + k, z, "end_rod[facing=up]") if k == 2 else d.set(x, y + k, z, "white_concrete")
        d.set(x, y + 3, z, "sea_lantern")
        return
    post = "dark_oak_fence" if kind == "hw" else "spruce_fence"
    d.set(x, y, z, "stone_bricks" if kind == "hw" else "cobblestone")
    for k in (1, 2):
        d.set(x, y + k, z, fence(post.replace("_fence", "")))
    d.set(x, y + 3, z, lantern(False))


def bench(d, x, z, y, along, back, wood, n=2, sit=False):
    pts = run(x, z, along, n)
    for cx, cz in pts:
        d.chair(cx, y, cz, back, wood, sit)
    for (cx, cz), side in ((pts[0], OPP[along]), (pts[-1], along)):
        ox, oz = D4[side]
        if d.air(cx + ox, y, cz + oz):
            d.set(cx + ox, y, cz + oz, trap(wood, side, "bottom", True))


def wagon(d, x, z, y, wood, load="hay_block[axis=x]"):
    """Farm wagon along x: plank bed on top slabs, trapdoor wheels, a load and a shaft."""
    for i in range(3):
        d.set(x + i, y, z, slab(wood, "top"))
        if load:
            d.set(x + i, y + 1, z, load if i < 2 else "composter[level=8]")
    for i in (0, 2):
        d.set(x + i, y, z - 1, trap(wood, "north", "bottom", True))
        d.set(x + i, y, z + 1, trap(wood, "south", "bottom", True))
    d.set(x + 3, y, z, fence(wood))


def lane(d, x1, z1, x2, z2, block, border=None):
    for x, z in cells(x1, z1, x2, z2):
        d.set(x, d.gy, z, block)
    if border:
        for x, z in cells(x1, z1, x2, z2):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, d.gy, z, border)


# ============================================================================================ outbuildings
SHELL = {
    "Hearthwood": dict(wood="dark_oak", floor="spruce_planks", roof="deepslate_tile", light="lantern"),
    "Cascadia": dict(wood="spruce", floor="spruce_planks", roof="dark_oak", light="lantern"),
    "Neoterra": dict(wood="birch", floor="polished_andesite", roof="smooth_quartz", light="sea_lantern"),
}


def outbuilding(d, x1, z1, x2, z2, kind, door_x=None, h=4, roof_axis=None):
    """Shell of a single-storey outbuilding (walls, floor, roof, door in the north wall, window openings).
    `kind` only picks the construction (barn / stable / garage get double doors, greenhouse / poolhouse are
    glazed). The caller furnishes every building by hand with fit()."""
    pack = d.pack
    S = SHELL[pack]
    W = S["wood"]
    y0 = d.gy + 1
    yt = y0 + h - 1
    door_x = door_x if door_x is not None else (x1 + x2) // 2
    glass = kind in ("greenhouse", "poolhouse")
    if pack == "Hearthwood":
        if glass:
            brick_walls(d, x1, z1, x2, z2, y0, y0, "bricks", None)
            for y in range(y0 + 1, yt + 1):
                for x, z in cells(x1, z1, x2, z2):
                    if x in (x1, x2) or z in (z1, z2):
                        d.set(x, y, z, "glass" if (x - x1) % 3 and (z - z1) % 3 else log("dark_oak_log", "y"))
        else:
            brick_walls(d, x1, z1, x2, z2, y0, y0, "stone_bricks", None)
            hw_walls(d, x1, z1, x2, z2, y0 + 1, yt, "spruce_planks" if kind in ("barn", "stable") else "calcite",
                     "dark_oak_log", 3)
    elif pack == "Cascadia":
        if glass:
            log_walls(d, x1, z1, x2, z2, y0, y0, "stripped_spruce_log", "spruce_log")
            for y in range(y0 + 1, yt + 1):
                for x, z in cells(x1, z1, x2, z2):
                    if x in (x1, x2) or z in (z1, z2):
                        d.set(x, y, z, "glass" if (x - x1) % 3 and (z - z1) % 3 else log("spruce_log", "y"))
        else:
            log_walls(d, x1, z1, x2, z2, y0, yt, "stripped_spruce_log" if kind != "barn" else "spruce_planks",
                      "spruce_log")
    else:
        nt_box(d, x1, z1, x2, z2, y0, yt, "white_concrete" if not glass else "glass",
               "light_gray_concrete")
    d.fill(x1 + 1, d.gy, z1 + 1, x2 - 1, d.gy, z2 - 1, S["floor"] if kind != "greenhouse" else "coarse_dirt")
    d.clear(x1 + 1, y0, z1 + 1, x2 - 1, yt, z2 - 1)
    # roof
    axis = roof_axis or ("x" if x2 - x1 >= z2 - z1 else "z")
    if pack == "Neoterra":
        d.flat(x1, z1, x2, z2, yt + 1, "smooth_quartz" if not glass else "glass", "white_concrete",
               "smooth_quartz_slab")
        for x in range(x1, x2 + 1):
            d.set(x, yt, z1, "cyan_terracotta") if not glass else None
        if kind != "greenhouse":
            for x in range(x1 + 2, x2 - 1, 2):
                for z in range(z1 + 2, z2 - 1, 3):
                    d.set(x, yt + 2, z, "daylight_detector[inverted=false,power=0]")
    else:
        rb = S["roof"]
        if glass:
            ridge = d.gable(x1, z1, x2, z2, yt + 1, axis, f"{rb}_stairs", f"{rb}_slab",
                            "glass", overhang=1)
        else:
            end = "spruce_planks" if pack == "Cascadia" else ("spruce_planks" if kind in ("barn", "stable")
                                                               else "calcite")
            ridge = d.gable(x1, z1, x2, z2, yt + 1, axis, f"{rb}_stairs", f"{rb}_slab", end, overhang=1)
    # door + windows
    if kind in ("barn", "stable", "garage"):
        d.double_door(door_x - 1 if door_x - 1 > x1 else door_x, y0, z1, "x", "south", "spruce" if pack != "Neoterra"
                      else "birch")
    else:
        d.door(door_x, y0, z1, "south", W)
    if not glass:
        for x in range(x1 + 2, x2 - 1, 3):
            if abs(x - door_x) > 1:
                d.window(x, y0 + 1, z1, x, y0 + 1, z1)
                d.window(x, y0 + 1, z2, x, y0 + 1, z2)
        for z in range(z1 + 2, z2 - 1, 3):
            d.window(x1, y0 + 1, z, x1, y0 + 1, z)
            d.window(x2, y0 + 1, z, x2, y0 + 1, z)
    return d


def well(d, x, z, pack):
    y = d.gy + 1
    rim = {"Hearthwood": "stone_bricks", "Cascadia": "cobblestone", "Neoterra": "smooth_quartz"}[pack]
    W = SHELL[pack]["wood"]
    for ax, az in cells(x - 1, z - 1, x + 1, z + 1):
        d.set(ax, y, az, rim if (ax, az) != (x, z) else "water")
        d.set(ax, d.gy, az, rim)
    for ax, az in ((x - 1, z - 1), (x + 1, z + 1), (x - 1, z + 1), (x + 1, z - 1)):
        pass
    for ax in (x - 1, x + 1):
        d.set(ax, y + 1, z, fence(W))
        d.set(ax, y + 2, z, fence(W))
    rb = SHELL[pack]["roof"]
    if pack != "Neoterra":
        d.set(x - 1, y + 3, z, stair(rb, "east"))
        d.set(x + 1, y + 3, z, stair(rb, "west"))
        d.set(x, y + 3, z, slab(rb))
        d.set(x, y + 2, z, "chain[axis=y,waterlogged=false]")
    else:
        d.set(x - 1, y + 3, z, slab("smooth_quartz"))
        d.set(x, y + 3, z, slab("smooth_quartz"))
        d.set(x + 1, y + 3, z, slab("smooth_quartz"))


def hedge(d, x1, z1, x2, z2, kind="oak", gaps=()):
    for x, z in cells(x1, z1, x2, z2):
        if (x in (x1, x2) or z in (z1, z2)) and (x, z) not in gaps:
            d.set(x, d.gy + 1, z, f"{kind}_leaves[distance=1,persistent=true,waterlogged=false]")


def pond(d, x1, z1, x2, z2, edge="grass_block[snowy=false]"):
    for x, z in cells(x1, z1, x2, z2):
        corner = x in (x1, x2) and z in (z1, z2)
        if corner:
            continue
        d.set(x, d.gy, z, "water")
        d.set(x, d.gy - 1, z, "clay")
    for x, z in ((x1 + 1, z1 + 1), (x2 - 1, z2 - 1)):
        d.set(x, d.gy + 1, z, "lily_pad")


# ============================================================================================ compositions: HOUSE



@design("house")
def house(pack, rel, L):
    return finish_decor({"Hearthwood": house_estate_hw, "Cascadia": house_estate_ca,
                         "Neoterra": house_estate_nt}[pack](rel, L), "house")


# ============================================================================================ compositions: COTTAGE



@design("cottage")
def cottage(pack, rel, L):
    return finish_decor({"Hearthwood": cottage_hamlet_hw, "Cascadia": cottage_retreat_ca,
                         "Neoterra": cottage_pavilions_nt}[pack](rel, L), "cottage")


# ============================================================================================ compositions: APARTMENT
def apartment_towers_nt(rel, L):
    """Residential towers on a landscaped podium: one tower that climbs, then a second and third tower of
    different heights, linked by a glass-canopied lobby walk, pool deck and planters."""
    d = Design("Neoterra", rel, (62, 80, 26), paving="smooth_stone")
    A = {1: 2, 2: 4, 3: 5, 4: 8, 5: 11}[L]
    stamp(d, apartment_nt(rel, L, A), 0, 0, primary=True)
    if L >= 3:
        t = apartment_nt(rel, 3, {3: 3, 4: 5, 5: 8}[L], v=1)
        recolor(t, [("white_concrete", "light_gray_concrete"), ("cyan_terracotta", "yellow_terracotta"),
                    ("light_gray_stained_glass_pane", "gray_stained_glass_pane")])
        stamp(d, t, 22, 0)
    if L >= 5:
        t = apartment_nt(rel, 3, 5, v=2)
        recolor(t, [("white_concrete", "white_terracotta"), ("cyan_terracotta", "orange_terracotta"),
                    ("light_gray_concrete", "polished_blackstone")])
        stamp(d, t, 44, 0)
    if L >= 3:
        # podium walk between the towers: canopy on slim columns, planters, benches
        for x in range(14, 25 if L < 5 else 47):
            for z in (21, 22, 23):
                d.set(x, 1, z, "polished_diorite" if (x + z) % 2 else "smooth_stone")
            d.set(x, 5, 22, slab("smooth_quartz", "top"))
            d.set(x, 5, 21, slab("smooth_quartz", "top"))
            d.set(x, 5, 23, slab("smooth_quartz", "top"))
            if x % 4 == 0:
                for y in range(2, 5):
                    d.set(x, y, 23, "white_concrete")
        for x in range(15, 24 if L < 5 else 46, 5):
            bench(d, x, 20, 2, "east", "north", "birch")
            planter(d, x + 2, 19, x + 3, 19, 1)
    if L >= 4:
        for x, z in cells(14, 0, 22, 3):
            d.set(x, 1, z, "smooth_quartz")
        for x, z in cells(15, 1, 21, 2):
            d.set(x, 1, z, "water")
        for x in (14, 22):
            lamp_post(d, x, 4, 1, "nt")
    return d


def apartment_square_hw(rel, L):
    """Victorian mansion blocks round a garden square: the first block rises, then wings close three and finally
    four sides of the square."""
    d = Design("Hearthwood", rel, (64, 40, 58), paving="grass_block[snowy=false]")
    A = {1: 1, 2: 2, 3: 3, 4: 3, 5: 4}[L]
    stamp(d, apartment_hw(rel, L, A), 18, 0, primary=True)
    if L >= 3:
        w = apartment_hw(rel, 3, {3: 2, 4: 3, 5: 4}[L], False, v=1)
        recolor(w, [("bricks", "mud_bricks"), ("deepslate_tile", "granite")], parts=("stairs", "slab"))
        stamp(d, w, 45, 12, rot=3)
    if L >= 4:
        w = apartment_hw(rel, 3, 3 if L == 4 else 4, False, v=2)
        recolor(w, [("bricks", "white_terracotta"), ("deepslate_tile", "dark_prismarine")], parts=("stairs", "slab"))
        stamp(d, w, 0, 12, rot=1)
    if L >= 5:
        w = apartment_hw(rel, 3, 3, False, v=3)
        recolor(w, [("deepslate_tile", "mud_brick"), ("stone_bricks", "smooth_sandstone")], parts=("stairs", "slab"))
        stamp(d, w, 18, 39)
    if L >= 3:
        # the square: lawn, gravel walks, a fountain, lamp posts and benches
        for x, z in cells(22, 22, 40, 36):
            d.set(x, 1, z, "gravel" if x in (30, 31, 32) or z in (28, 29, 30) else "grass_block[snowy=false]")
        for x, z in cells(29, 27, 33, 31):
            d.set(x, 2, z, "stone_bricks" if x in (29, 33) or z in (27, 31) else "water")
        d.set(31, 3, 29, "stone_brick_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
        for x, z in ((24, 24), (38, 24), (24, 34), (38, 34)):
            lamp_post(d, x, z, 1)
        for x, z in ((25, 28), (36, 28)):
            bench(d, x, z, 2, "south", "east" if x < 30 else "west", "dark_oak")
        for x, z in ((23, 27), (39, 31)):
            tree(d, x, z, 2, "oak", 4, 2)
    return d


def apartment_rows_ca(rel, L):
    """Mill-town company housing: one boarding house with a gallery, then further boarding houses in two rows
    either side of a plank-walk street, with a bunkhouse and wood yard."""
    d = Design("Cascadia", rel, (63, 30, 44), paving="grass_block[snowy=false]")
    a = {1: (2, 1), 2: (2, 2), 3: (3, 2), 4: (3, 2), 5: (3, 2)}[L]
    m = apartment_ca(rel, L, *a)
    recolor(m, [("dark_oak", "dark_prismarine")])
    stamp(d, m, 0, 0, primary=True)
    if L >= 3:
        m = apartment_ca(rel, 3, 2, 1 if L == 3 else 2, v=1)
        recolor(m, [("dark_oak", "mangrove"), ("stripped_spruce_log", "stripped_mangrove_log")])
        stamp(d, m, 32, 0)
    if L >= 4:
        m = apartment_ca(rel, 3, 2 if L == 4 else 3, 2 if L == 5 else 1, v=2)
        recolor(m, [("dark_oak", "deepslate_tile"), ("stripped_spruce_log", "stripped_birch_log")])
        stamp(d, m, 0, 22)
    if L >= 5:
        m = apartment_ca(rel, 3, 3, 2, v=3)
        recolor(m, [("dark_oak", "cobbled_deepslate"), ("stripped_spruce_log", "stripped_dark_oak_log")])
        stamp(d, m, 32, 22)
    if L >= 3:
        for x in range(0, 63):
            for z in (19, 20, 21):
                d.set(x, 1, z, "spruce_planks" if z == 20 else "coarse_dirt")
        for x in (8, 24, 40, 56):
            lamp_post(d, x, 19, 1, "ca")
    if L == 4:
        # wood yard on the empty lot: stacked logs, a wagon, a chopping block
        for x, z in cells(21, 24, 31, 38):
            d.set(x, 1, z, "coarse_dirt" if (x * z) % 3 else "packed_mud")
        for z in (26, 30, 34):
            for x in range(22, 30):
                d.set(x, 2, z, log("spruce_log", "x"))
                if x % 3:
                    d.set(x, 3, z, log("spruce_log", "x"))
        wagon(d, 23, 37, 2, "spruce", log("spruce_log", "x"))
        d.set(30, 2, 28, log("stripped_spruce_log", "y"))
    return d


@design("apartment")
def apartment(pack, rel, L):
    return finish_decor({"Neoterra": apartment_towers_nt, "Hearthwood": apartment_square_hw,
                         "Cascadia": apartment_rows_ca}[pack](rel, L), "apartment")


# ============================================================================================ compositions: QUADPLEX
def quadplex_streets_hw(rel, L):
    """Tudor terraces: the first town cottage, a pair, the full terrace of four, then a second terrace across a
    shared green and finally a third terrace closing a little close."""
    d = Design("Hearthwood", rel, (60, 22, 48), paving="grass_block[snowy=false]")
    m = quadplex_hw(rel, L, {1: 1, 2: 2, 3: 4, 4: 4, 5: 4}[L])
    recolor(m, [("deepslate_tile", "brick")], parts=("full", "stairs", "slab"))
    stamp(d, m, 0, 0, primary=True)
    if L >= 4:
        m = quadplex_hw(rel, 3, 3 if L == 4 else 4, v=1)
        recolor(m, [("deepslate_tile", "granite"), ("calcite", "light_blue_terracotta"),
                    ("white_terracotta", "yellow_terracotta")])
        stamp(d, m, 30, 0)
    if L >= 5:
        m = quadplex_hw(rel, 3, 4, v=2)
        recolor(m, [("deepslate_tile", "mud_brick"), ("bricks", "stone_bricks"), ("calcite", "pink_terracotta")])
        stamp(d, m, 0, 26)
    if L >= 4:
        for x in range(0, 60):
            d.set(x, 1, 22, "gravel")
            d.set(x, 1, 23, "gravel")
        for x in (6, 20, 34, 48):
            lamp_post(d, x, 24, 1)
    return d


def quadplex_mews_nt(rel, L):
    """Modern townhouse mews: duplexes added in pairs, then a second staggered row and a back row across a
    planted mews court."""
    d = Design("Neoterra", rel, (63, 22, 42), paving="smooth_stone")
    m = quadplex_nt(rel, L, {1: 1, 2: 2, 3: 4, 4: 4, 5: 4}[L])
    recolor(m, [("cyan_terracotta", "lime_terracotta")])
    stamp(d, m, 0, 0, primary=True)
    if L >= 4:
        m = quadplex_nt(rel, 3, 3 if L == 4 else 4, v=1)
        recolor(m, [("white_concrete", "white_terracotta"), ("cyan_terracotta", "orange_terracotta"),
                    ("light_gray_concrete", "brown_terracotta")])
        stamp(d, m, 32, 0)
    if L >= 5:
        m = quadplex_nt(rel, 3, 4, v=2)
        recolor(m, [("white_concrete", "light_gray_concrete"), ("cyan_terracotta", "magenta_terracotta"),
                    ("light_gray_concrete", "gray_concrete")])
        stamp(d, m, 0, 22)
        m = quadplex_nt(rel, 3, 4)
        recolor(m, [("white_concrete", "smooth_quartz"), ("cyan_terracotta", "yellow_terracotta"),
                    ("light_gray_concrete", "polished_deepslate")])
        stamp(d, m, 32, 22)
    if L >= 4:
        for x in range(0, 63, 4):
            planter(d, x, 19, x + 1, 19, 1)
        for x in (3, 18, 33, 48):
            lamp_post(d, x, 20, 1, "nt")
    return d


@design("quadplex")
def quadplex(pack, rel, L):
    return finish_decor({"Hearthwood": quadplex_streets_hw, "Cascadia": quadplex_ca,
                         "Neoterra": quadplex_mews_nt}[pack](rel, L), "quadplex")


# ============================================================================================ player-house add-ons
def ph_shell(d, x1, z1, x2, z2, y1, y2, part="wall"):
    """Pack walls for player-house add-ons."""
    p = d.pack
    if p == "Hearthwood":
        brick_walls(d, x1, z1, x2, z2, y1, y2, "stone_bricks", "cobblestone", "chiseled_stone_bricks")
    elif p == "Cascadia":
        log_walls(d, x1, z1, x2, z2, y1, y2, "stripped_spruce_log", "spruce_log", footing=(y1 == d.gy + 1),
                  plinth=(y1 == d.gy + 1))
    else:
        nt_box(d, x1, z1, x2, z2, y1, y2, "white_concrete", "polished_blackstone")


def ph_tower(d, x1, z1, rooms):
    """7x7 tower, one storey per entry of `rooms` (each a hand-written list of (dx, dy, dz, block) relative to the
    tower's north-west corner and that floor's walking level), joined by a ladder in the north-west corner,
    door in the north wall. The last floor is glazed all round. Pyramid roof (flat glazed lantern in Neoterra)."""
    p = d.pack
    floors = len(rooms)
    x2, z2 = x1 + 6, z1 + 6
    W = SHELL[p]["wood"]
    H = 4
    top = d.gy + 1 + H * floors
    for f in range(floors):
        Y = d.gy + 1 + H * f
        ph_shell(d, x1, z1, x2, z2, Y, Y + H - 1)
        d.fill(x1 + 1, Y - 1, z1 + 1, x2 - 1, Y - 1, z2 - 1, f"{W}_planks" if p != "Neoterra" else "polished_diorite")
        d.clear(x1 + 1, Y, z1 + 1, x2 - 1, Y + H - 1, z2 - 1)
        for x in (x1 + 2, x1 + 4):
            if f:
                d.window(x, Y + 1, z1, x, Y + 2, z1)
            d.window(x, Y + 1, z2, x, Y + 2, z2)
        d.window(x1, Y + 1, z1 + 3, x1, Y + 2, z1 + 3)
        d.window(x2, Y + 1, z1 + 3, x2, Y + 2, z1 + 3)
        if f == floors - 1:                                  # lantern room glazed on all sides
            for x in (x1 + 1, x1 + 3, x1 + 5):
                for z in (z1, z2):
                    d.window(x, Y + 1, z, x, Y + 2, z)
        for dx, dy, dz, b in rooms[f]:
            d.set(x1 + dx, Y + dy, z1 + dz, b)
    for y in range(d.gy + 1, d.gy + 1 + H * (floors - 1) + 1):
        d.set(x1 + 1, y, z1 + 1, "ladder[facing=east,waterlogged=false]")
    d.door(x1 + 3, d.gy + 1, z1, "south", W)
    if p == "Neoterra":
        d.flat(x1, z1, x2, z2, top, "smooth_quartz", "glass", "smooth_quartz_slab")
        d.set(x1 + 3, top + 1, z1 + 3, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    else:
        rb = SHELL[p]["roof"]
        d.fill(x1 + 1, top, z1 + 1, x2 - 1, top, z2 - 1, f"{W}_planks")
        _spire(d, x1, z1, x2, z2, top, rb)
    return top


def tower_rooms(W, which):
    """Hand-written floor programmes for the estate towers (interior dx/dz 1..5, ladder at (1,1), door (3,0))."""
    TS = slab(W, "top")
    light = (3, 2, 3, LANT)
    shelf = lambda dx, dz: [(dx, dy, dz, "bookshelf") for dy in (0, 1, 2)]
    if which == "lore":           # library tower: library, still-room, study, star room
        return [
            shelf(5, 1) + shelf(5, 2) + shelf(5, 4) + shelf(5, 5) + [
                (5, 0, 3, "lectern[facing=west,has_book=false,powered=false]"), (2, 0, 3, TS), (2, 0, 4, stair(W, "south")),
                (2, 1, 3, "candle[candles=3,lit=false,waterlogged=false]"), (3, 0, 5, "potted_fern"),
                (3, 0, 2, "purple_carpet"), (3, 0, 3, "purple_carpet"), (4, 0, 3, "purple_carpet"), light],
            [(5, 0, 2, TS), (5, 1, 2, "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]"),
             (5, 0, 3, CAUL), (5, 0, 4, TS), (5, 1, 4, "brewing_stand[has_bottle_0=false,has_bottle_1=true,has_bottle_2=true]"),
             (5, 0, 5, BRL("west")), (3, 0, 5, "cauldron"), (2, 0, 5, BRL("north")), (4, 0, 5, POT),
             (3, 0, 3, "green_carpet"), (4, 0, 3, "green_carpet"), light],
            [(5, 0, 2, TS), (5, 0, 3, TS), (5, 1, 2, "candle[candles=2,lit=false,waterlogged=false]"),
             (4, 0, 3, stair(W, "west")), (5, 0, 5, "cartography_table"), (3, 0, 5, CHEST("north")),
             (5, 0, 4, "bookshelf"), (2, 0, 3, "blue_carpet"), (3, 0, 3, "blue_carpet"), light],
            [(3, 0, 3, fence(W)), (3, 1, 3, "end_rod[facing=north]"), (4, 0, 5, stair(W, "south")),
             (2, 0, 5, "cartography_table"), (5, 0, 5, CHEST("west"))]]
    if which == "guard":          # armoury tower: armoury, archive, map room, still-room, beacon room
        return [
            [(5, 0, 2, "smithing_table"), (5, 0, 3, "anvil[facing=north]"), (5, 0, 4, GRIND("west")),
             (5, 1, 2, "red_wall_banner[facing=west]"), (5, 1, 4, "red_wall_banner[facing=west]"),
             (3, 0, 5, CHEST("north")), (2, 0, 5, BRL("north")), (4, 0, 5, BRL("north")), light],
            shelf(5, 2) + shelf(5, 3) + shelf(5, 4) + [(2, 0, 5, CHEST("north")), (3, 0, 5, CHEST("north")),
                                                     (4, 0, 5, CHEST("north")), (3, 0, 3, "brown_carpet"), light],
            [(4, 0, 3, "cartography_table"), (4, 0, 4, stair(W, "south")),
             (5, 0, 2, "lectern[facing=west,has_book=false,powered=false]"), (5, 1, 4, "blue_wall_banner[facing=west]"),
             (2, 0, 5, "potted_fern"), (3, 0, 2, "white_carpet"), (3, 0, 3, "white_carpet"), light],
            [(5, 0, 3, CAUL), (5, 0, 4, TS), (5, 1, 4, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]"),
             (2, 0, 5, BRL("north")), (3, 0, 5, BRL("north")), (4, 0, 5, "composter[level=5]"), light],
            [(3, 0, 3, fence(W)), (3, 1, 3, "end_rod[facing=south]"), (2, 0, 2, stair(W, "west")),
             (5, 0, 5, "cartography_table")]]
    if which == "rest":           # garden tower: guest bedroom, sitting room, music room, belvedere
        return [
            [(5, 0, 5, "red_bed[facing=east,occupied=false,part=head]"),
             (4, 0, 5, "red_bed[facing=east,occupied=false,part=foot]"), (5, 0, 4, TS),
             (5, 1, 4, "candle[candles=1,lit=false,waterlogged=false]"), (2, 0, 5, CHEST("north")),
             (3, 0, 3, "red_carpet"), (4, 0, 3, "red_carpet"), light],
            [(4, 0, 4, stair(W, "south")), (5, 0, 4, stair(W, "south")), (4, 0, 2, slab(W)), (2, 0, 5, "bookshelf"),
             (3, 0, 5, "potted_azalea_bush"), (3, 0, 3, "green_carpet"), light],
            [(4, 0, 4, "note_block[instrument=harp,note=5,powered=false]"), (3, 0, 4, stair(W, "east")),
             (5, 0, 2, "jukebox"), (2, 0, 5, "potted_fern"), light],
            [(2, 0, 5, stair(W, "south")), (4, 0, 5, stair(W, "south")), (3, 0, 5, slab(W, "top")),
             (3, 1, 5, "potted_red_tulip")]]
    return [                      # watch tower: trophy room, guard room, lookout
        [(5, 0, 2, BRL("west")),
         (5, 1, 3, "green_wall_banner[facing=west]"), (5, 0, 4, CHEST("west")), (3, 0, 5, stair(W, "south")),
         (2, 0, 5, "potted_fern"), (3, 0, 3, "brown_carpet"), light],
        [(5, 0, 5, "brown_bed[facing=south,occupied=false,part=head]"),
         (5, 0, 4, "brown_bed[facing=south,occupied=false,part=foot]"), (4, 0, 5, TS), (2, 0, 5, BRL("north")),
         (3, 0, 3, slab(W, "top")), (3, 0, 4, stair(W, "south")), light],
        [(3, 0, 5, stair(W, "south")), (5, 0, 3, fence(W)), (5, 1, 3, LANTF)]]

def _spire(d, x1, z1, x2, z2, y, rb):
    """Steep pyramid roof: rings of stairs, two layers per ring, finial on top."""
    i, yy = 0, y
    while x1 - 1 + i <= x2 + 1 - i:
        a1, a2, b1, b2 = x1 - 1 + i, x2 + 1 - i, z1 - 1 + i, z2 + 1 - i
        if a2 - a1 < 1:
            d.set(a1, yy, b1, f"{rb}_slab[type=bottom,waterlogged=false]" if not rb.endswith("planks") else rb)
            d.set(a1, yy + 1, b1, "lightning_rod[facing=up,powered=false,waterlogged=false]")
            break
        for x, z in cells(a1, b1, a2, b2):
            if x in (a1, a2) or z in (b1, b2):
                f = "south" if z == b1 else "north" if z == b2 else "east" if x == a1 else "west"
                shape = "straight"
                if x in (a1, a2) and z in (b1, b2):
                    shape = "outer_left" if (x == a1) == (z == b1) else "outer_right"
                    f = "south" if z == b1 else "north"
                d.set(x, yy, z, f"{rb}_stairs[facing={f},half=bottom,shape={shape},waterlogged=false]")
                if i > 0:
                    d.set(x, yy - 1, z, f"{rb}_stairs[facing={f},half=bottom,shape={shape},waterlogged=false]"
                          if d.air(x, yy - 1, z) else d.get(x, yy - 1, z))
        i += 1
        yy += 2


def ph_hall(d, x1, z1, x2, z2, h=6, hearths=True):
    """Shell of a tall hall: walls, tall windows, roof with tie beams, double door in the north wall and (optionally)
    a hearth at each end. Furnished by hand at the call site."""
    p = d.pack
    W = SHELL[p]["wood"]
    y0 = d.gy + 1
    yt = y0 + h - 1
    ph_shell(d, x1, z1, x2, z2, y0, yt)
    d.fill(x1 + 1, d.gy, z1 + 1, x2 - 1, d.gy, z2 - 1, "polished_andesite" if p == "Neoterra" else
           f"{W}_planks" if p == "Cascadia" else "stone_bricks")
    d.clear(x1 + 1, y0, z1 + 1, x2 - 1, yt, z2 - 1)
    for x in range(x1 + 2, x2 - 1, 3):
        d.window(x, y0 + 2, z1, x, yt - 1, z1)
        d.window(x, y0 + 2, z2, x, yt - 1, z2)
    if p == "Neoterra":
        d.flat(x1, z1, x2, z2, yt + 1, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
        for x in range(x1 + 2, x2 - 1, 3):
            for z in range(z1 + 2, z2 - 1, 3):
                d.set(x, yt + 1, z, "glass")
    else:
        rb = SHELL[p]["roof"]
        d.gable(x1, z1, x2, z2, yt + 1, "x", f"{rb}_stairs", f"{rb}_slab",
                "stone_bricks" if p == "Hearthwood" else log("stripped_spruce_log", "z"))
        for x in range(x1 + 2, x2 - 1, 4):                         # tie beams
            for z in range(z1 + 1, z2):
                d.set(x, yt, z, log("dark_oak_log" if p == "Hearthwood" else "spruce_log", "z"))
    door = (x1 + x2) // 2
    d.double_door(door, y0, z1, "x", "south", W)
    for y in (y0 + 2,):
        d.set(door, y, z1, "chiseled_stone_bricks" if p == "Hearthwood" else d.get(door, y, z1))
    # hearths at both ends
    zc = (z1 + z2) // 2
    fire = "soul_campfire" if p == "Neoterra" else "campfire"
    frame = {"Hearthwood": "stone_bricks", "Cascadia": "cobblestone", "Neoterra": "polished_blackstone_bricks"}[p]
    if hearths:
        fireplace(d, x1, zc, y0, "east", yt + 4, frame, frame, fire)
        fireplace(d, x2, zc, y0, "west", yt + 4, frame, frame, fire)
    return zc

def ph_vault(d, x1, z1, x2, z2, h=4):
    """Storehouse shell; the shelving is placed by hand at the call site."""
    p = d.pack
    W = SHELL[p]["wood"]
    y0 = d.gy + 1
    yt = y0 + h - 1
    ph_shell(d, x1, z1, x2, z2, y0, yt)
    d.fill(x1 + 1, d.gy, z1 + 1, x2 - 1, d.gy, z2 - 1, SHELL[p]["floor"])
    d.clear(x1 + 1, y0, z1 + 1, x2 - 1, yt, z2 - 1)
    if p == "Neoterra":
        d.flat(x1, z1, x2, z2, yt + 1, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
    else:
        rb = SHELL[p]["roof"]
        d.gable(x1, z1, x2, z2, yt + 1, "x", f"{rb}_stairs", f"{rb}_slab",
                "stone_bricks" if p == "Hearthwood" else "spruce_planks")
    d.double_door((x1 + x2) // 2, y0, z1, "x", "south", W)
    return d


# ============================================================================================ compositions: PLAYER HOUSE
def player_estate(rel, L):
    """The player's seat grows into an estate: the house with its stores and workshop (L1-2), then a library
    tower in a walled garden, a great hall for feasts, and finally a second tower and a storehouse vault."""
    pack = REQ_PACK[0]
    d = Design(pack, rel, (64, 50, 64), paving="grass_block[snowy=false]" if pack != "Neoterra" else "smooth_stone")
    fn = {"Hearthwood": playerhouse_hw, "Cascadia": playerhouse_ca, "Neoterra": playerhouse_nt}[pack]
    main = fn(rel, L)
    recolor(main, {"Hearthwood": [("deepslate_tile", "dark_prismarine")],
                   "Cascadia": [("dark_oak", "deepslate_tile")],
                   "Neoterra": [("cyan_terracotta", "magenta_terracotta"),
                                ("light_gray_concrete", "polished_blackstone")]}[pack])
    stamp(d, main, 0, 0, primary=True)
    pal_tower = {"Hearthwood": [], "Cascadia": [("dark_oak", "mangrove")],
                 "Neoterra": [("white_concrete", "white_terracotta")]}[pack]
    pal_hall = {"Hearthwood": [("deepslate_tile", "brick")], "Cascadia": [("dark_oak", "dark_prismarine")],
                "Neoterra": [("white_concrete", "light_gray_concrete"), ("polished_blackstone", "polished_deepslate")]}[pack]
    pal_vault = {"Hearthwood": [("deepslate_tile", "mud_brick")], "Cascadia": [("dark_oak", "cobbled_deepslate")],
                 "Neoterra": [("white_concrete", "gray_concrete")]}[pack]
    lamp = {"Hearthwood": "hw", "Cascadia": "ca", "Neoterra": "nt"}[pack]
    W = SHELL[pack]["wood"]
    path_b = {"Hearthwood": "gravel", "Cascadia": "coarse_dirt", "Neoterra": "polished_diorite"}[pack]
    if pack == "Hearthwood":
        T1, G, HALL, VAULT, T2 = (36, 2), (33, 11, 62, 28), (33, 32, 62, 44), (2, 34, 24, 46), (55, 2)
    elif pack == "Cascadia":
        T1, G, HALL, VAULT, T2 = (34, 26), (42, 22, 62, 40), (33, 2, 62, 14), (2, 34, 24, 46), (34, 44)
    else:
        T1, G, HALL, VAULT, T2 = (32, 34), (40, 34, 62, 50), (32, 2, 62, 12), (2, 34, 26, 46), (32, 52)
    if L >= 3:
        ph_tower(d, T1[0], T1[1], tower_rooms(W, "lore"))
        recolor(d, pal_tower, (T1[0] - 1, T1[1] - 1, T1[0] + 7, T1[1] + 7, 2))
        gx1, gz1, gx2, gz2 = G
        hedge(d, gx1, gz1, gx2, gz2, "oak" if pack != "Cascadia" else "spruce",
              gaps=((gx1, (gz1 + gz2) // 2), ((gx1 + gx2) // 2, gz1)))
        cx, cz = (gx1 + gx2) // 2, (gz1 + gz2) // 2
        for x in range(gx1 + 1, gx2):
            d.set(x, 1, cz, path_b)
        for z in range(gz1 + 1, gz2):
            d.set(cx, 1, z, path_b)
        for ax, az in cells(cx - 1, cz - 1, cx + 1, cz + 1):
            d.set(ax, 2, az, "stone_bricks" if (ax, az) != (cx, cz) else "water")
        for x, z in ((gx1 + 3, gz1 + 3), (gx2 - 3, gz1 + 3), (gx1 + 3, gz2 - 3), (gx2 - 3, gz2 - 3)):
            tree(d, x, z, 2, "oak" if pack != "Cascadia" else "spruce", 4, 2)
        for x, z in ((cx - 4, cz - 1), (cx + 3, cz + 1)):
            bench(d, x, z, 2, "east", "north" if z < cz else "south", W)
        for x in range(gx1 + 2, gx2 - 1, 2):
            for z in (gz1 + 1, gz2 - 1):
                d.set(x, 2, z, ("rose_bush[half=lower]", "peony[half=lower]", "lilac[half=lower]")[x % 3])
                d.set(x, 3, z, ("rose_bush[half=upper]", "peony[half=upper]", "lilac[half=upper]")[x % 3])
    if L >= 4:
        ph_hall(d, *HALL, h=7)
        hall_furniture(d, pack, W)
        recolor(d, pal_hall, (HALL[0] - 2, HALL[1] - 1, HALL[2] + 2, HALL[3] + 1, 2))
        hx = (HALL[0] + HALL[2]) // 2
        for x in (HALL[0], HALL[2]):
            lamp_post(d, x, HALL[1] - 2 if HALL[1] > 3 else HALL[3] + 2, 1, lamp)
        ph_vault(d, *VAULT, h=4)
        # shelving: a back bay of barrels three high (gap opposite the doors), an island bay down the middle,
        # chests along the west wall, two lanterns over the aisles
        xe = VAULT[2] - 1                                   # 23 (HW, CA) / 25 (NT)
        dx = (VAULT[0] + VAULT[2]) // 2                     # door column 13 / 14
        for x in [x for x in range(3, xe + 1) if abs(x - dx) > 1]:
            for k in range(3):
                d.set(x, 2 + k, 45, BRL("north"))
        for x in range(5, xe - 1):
            for k in range(3):
                d.set(x, 2 + k, 40, BRL("north"))
        fit(d, [(3, 2, z, CHEST("east")) for z in (36, 37, 38, 42, 43, 44)]
            + ([(8, 5, 37, LANT), (18, 5, 37, LANT)] if pack != "Neoterra" else
               [(8, 6, 37, "sea_lantern"), (18, 6, 37, "sea_lantern")]))
        recolor(d, pal_vault, (VAULT[0] - 1, VAULT[1] - 1, VAULT[2] + 1, VAULT[3] + 1, 2))
        for x in range(VAULT[0], VAULT[2] + 1, 6):
            lamp_post(d, x, VAULT[1] - 2, 1, lamp)
    if L >= 5:
        ph_tower(d, T2[0], T2[1], tower_rooms(W, "guard"))
        recolor(d, pal_tower, (T2[0] - 1, T2[1] - 1, T2[0] + 7, T2[1] + 7, 2))
        ph_tower(d, 2, 50, tower_rooms(W, "rest"))
        T3 = {"Hearthwood": (42, 50), "Cascadia": (50, 50), "Neoterra": (50, 54)}[pack]
        ph_tower(d, T3[0], T3[1], tower_rooms(W, "watch"))
        ph_hall(d, 12, 50, 30, 61, h=5, hearths=False)
        # estate chapel: pews either side of the aisle facing the altar, candles, banners
        for z in (53, 55, 57):
            for x in (14, 15, 16, 17, 18, 19, 24, 25, 26, 27, 28, 29):
                d.set(x, 2, z, stair(W, "north"))
        fit(d, [(20, 2, 60, "chiseled_stone_bricks"), (21, 2, 60, "chiseled_stone_bricks"),
                (22, 2, 60, "chiseled_stone_bricks"), (20, 3, 60, "candle[candles=3,lit=false,waterlogged=false]"),
                (22, 3, 60, "candle[candles=3,lit=false,waterlogged=false]"), (21, 3, 60, POT),
                (21, 2, 58, "lectern[facing=north,has_book=false,powered=false]"),
                (14, 4, 60, "white_wall_banner[facing=north]"), (28, 4, 60, "white_wall_banner[facing=north]"),
                (17, 6, 55, CHAIN), (17, 5, 55, LANT), (26, 6, 55, CHAIN), (26, 5, 55, LANT),
                (13, 2, 51, "potted_fern"), (29, 2, 51, "potted_fern")])
        recolor(d, pal_vault, (10, 49, 32, 62, 2))
        # estate wall with a gate on the street and piers with lamps
        wall = {"Hearthwood": "stone_brick_wall", "Cascadia": "cobblestone_wall", "Neoterra": "polished_blackstone_wall"}[pack]
        ws = f"{wall}[east=low,north=none,south=none,up=false,waterlogged=false,west=low]"
        for x in range(0, 64):
            if d.air(x, 2, 0) and not (12 <= x <= 14):
                d.set(x, 2, 0, ws)
        for z in range(0, 64):
            for x in (0, 63):
                if d.air(x, 2, z):
                    d.set(x, 2, z, f"{wall}[east=none,north=low,south=low,up=false,waterlogged=false,west=none]")
        for x in range(0, 64):
            if d.air(x, 2, 63):
                d.set(x, 2, 63, ws)
        for x in range(0, 64, 8):
            for z in (0, 63):
                if d.get(x, 2, z).startswith("minecraft:" + wall):
                    d.set(x, 2, z, f"{wall}[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
                    d.set(x, 3, z, lantern(False))
    return d


def hall_furniture(d, pack, W):
    """Hand-placed furniture of each pack's great hall (coordinates of that pack's HALL rectangle)."""
    TS = slab(W, "top")
    if pack == "Hearthwood":        # feast hall x34..61 z33..43: two long tables, high table on the east, banners
        for z in (36, 40):
            for x in range(37, 58):
                d.set(x, 2, z, TS)
                d.set(x, 2, z - 1, stair(W, "north"))
                d.set(x, 2, z + 1, stair(W, "south"))
        for z in range(36, 41):
            d.set(59, 2, z, TS)
            d.set(60, 2, z, stair(W, "east"))
        fit(d, [(40, 3, 36, "candle[candles=3,lit=false,waterlogged=false]"), (47, 3, 40, POT),
                (54, 3, 36, "candle[candles=3,lit=false,waterlogged=false]"), (59, 3, 38, POT),
                (40, 7, 38, CHAIN), (40, 8, 38, CHAIN), (40, 6, 38, LANT), (47, 7, 38, CHAIN), (47, 8, 38, CHAIN),
                (47, 6, 38, LANT), (54, 7, 38, CHAIN), (54, 8, 38, CHAIN), (54, 6, 38, LANT),
                (38, 5, 43, "red_wall_banner[facing=north]"), (47, 5, 43, "red_wall_banner[facing=north]"),
                (56, 5, 43, "red_wall_banner[facing=north]"), (35, 2, 42, BRL("north")), (36, 2, 42, BRL("north"))])
    elif pack == "Cascadia":        # lodge hall x34..61 z3..13: crosswise bench tables, bear rug, keg corner
        for x in (40, 54):
            for z in range(5, 12):
                d.set(x, 2, z, TS)
                d.set(x - 1, 2, z, stair(W, "west"))
                d.set(x + 1, 2, z, stair(W, "east"))
        rugc(d, 45, 7, 50, 9, 2, "brown")
        fit(d, [(60, 2, 12, BRL("north")), (61, 2, 12, BRL("north")), (61, 3, 12, BRL()), (60, 2, 11, slab(W, "top")),
                (47, 7, 8, CHAIN), (47, 8, 8, CHAIN), (47, 6, 8, LANT), (40, 7, 8, CHAIN), (40, 6, 8, LANT),
                (54, 7, 8, CHAIN), (54, 6, 8, LANT), (37, 5, 13, "green_wall_banner[facing=north]"),
                (47, 5, 13, "green_wall_banner[facing=north]"), (57, 5, 13, "green_wall_banner[facing=north]"),
                (40, 3, 8, "candle[candles=2,lit=false,waterlogged=false]"), (54, 3, 8, POT)])
    else:                           # banquet gallery x33..61 z3..11: round tables, a bar on the back wall
        for tx, tz in ((38, 5), (38, 9), (44, 9), (52, 9), (56, 5), (56, 9)):
            d.set(tx, 2, tz, slab("smooth_quartz", "top"))
            d.set(tx, 3, tz, "potted_azure_bluet" if tx % 4 else "candle[candles=3,lit=false,waterlogged=false]")
            for dx, dz, back in ((0, -1, "north"), (0, 1, "south"), (-1, 0, "west"), (1, 0, "east")):
                d.set(tx + dx, 2, tz + dz, stair(W, back))
        for x in range(45, 51):
            d.set(x, 2, 11, slab("smooth_quartz", "top"))
        fit(d, [(44, 2, 11, BRL("north")), (51, 2, 11, BRL("north")), (47, 3, 11, POT),
                (40, 9, 7, "sea_lantern"), (47, 9, 7, "sea_lantern"), (54, 9, 7, "sea_lantern"),
                (36, 5, 11, "cyan_wall_banner[facing=north]"), (58, 5, 11, "cyan_wall_banner[facing=north]")])


REQ_PACK = [None]


@design("playerhouse")
def playerhouse(pack, rel, L):
    REQ_PACK[0] = pack
    return finish_decor(player_estate(rel, L), "playerhouse")


# ============================================================================================ palette variety
FAM = {
    "deepslate_tile": ("deepslate_tiles", "deepslate_tile_stairs", "deepslate_tile_slab", "deepslate_tile_wall"),
    "brick": ("bricks", "brick_stairs", "brick_slab", "brick_wall"),
    "mud_brick": ("mud_bricks", "mud_brick_stairs", "mud_brick_slab", "mud_brick_wall"),
    "dark_prismarine": ("dark_prismarine", "dark_prismarine_stairs", "dark_prismarine_slab", "prismarine_wall"),
    "granite": ("polished_granite", "polished_granite_stairs", "polished_granite_slab", "granite_wall"),
    "cobbled_deepslate": ("cobbled_deepslate", "cobbled_deepslate_stairs", "cobbled_deepslate_slab",
                          "cobbled_deepslate_wall"),
    "stone_brick": ("stone_bricks", "stone_brick_stairs", "stone_brick_slab", "stone_brick_wall"),
    "spruce": ("spruce_planks", "spruce_stairs", "spruce_slab", None),
    "dark_oak": ("dark_oak_planks", "dark_oak_stairs", "dark_oak_slab", None),
    "mangrove": ("mangrove_planks", "mangrove_stairs", "mangrove_slab", None),
    "cherry": ("cherry_planks", "cherry_stairs", "cherry_slab", None),
    "warped": ("warped_planks", "warped_stairs", "warped_slab", None),
    "birch": ("birch_planks", "birch_stairs", "birch_slab", None),
    "smooth_quartz": ("smooth_quartz", "smooth_quartz_stairs", "smooth_quartz_slab", None),
    "cut_copper": ("waxed_cut_copper", "waxed_cut_copper_stairs", "waxed_cut_copper_slab", None),
}


def recolor(d, pairs, box=None, parts=("stairs", "slab")):
    """Swap material families in `d` (optionally only inside box=(x1,z1,x2,z2[,y1])):
    pairs = [(src, dst)] where src/dst are FAM keys (only the given parts: full/stairs/slab/wall) or plain
    block ids (exact block swap, properties kept)."""
    table = {}
    for src, dst in pairs:
        if src in FAM and dst in FAM:
            for i, part in enumerate(("full", "stairs", "slab", "wall")):
                if part in parts and FAM[src][i] and FAM[dst][i]:
                    table["minecraft:" + FAM[src][i]] = "minecraft:" + FAM[dst][i]
        else:
            table["minecraft:" + src] = "minecraft:" + dst
    bp = d.bp
    x1, z1, x2, z2 = (box[:4] if box else (0, 0, bp.sx - 1, bp.sz - 1))
    y1 = box[4] if box and len(box) > 4 else 0
    for y in range(y1, bp.sy):
        layer = bp.grid[y]
        for z in range(max(0, z1), min(bp.sz - 1, z2) + 1):
            row = layer[z]
            for x in range(max(0, x1), min(bp.sx - 1, x2) + 1):
                st = row[x]
                name = st.split("[")[0]
                if name in table:
                    row[x] = table[name] + st[len(name):]
    return d


# ============================================================================================ cottage / camp add-ons
def addon(d, x1, z1, x2, z2, kind, h=3):
    """Shell for the small cottage / camp outbuildings; kind "cartshed" has an open front on posts.
    Furnished by hand at the call site."""
    pack = d.pack
    y0 = d.gy + 1
    outbuilding(d, x1, z1, x2, z2, "empty", h=h)
    if kind == "cartshed":
        for x in range(x1 + 1, x2):
            for y in range(y0, y0 + h - 1):
                d.set(x, y, z1, AIR)
        for x in range(x1, x2 + 1, 3):
            for y in range(y0, y0 + h - 1):
                d.set(x, y, z1, log("spruce_log" if pack != "Hearthwood" else "dark_oak_log", "y"))
    elif kind in ("potting", "teahouse"):
        door_x = (x1 + x2) // 2
        for x in (door_x - 1, door_x + 1):
            d.window(x, y0 + 1, z1, x, y0 + 1, z1)
    elif kind == "store":
        d.sign((x1 + x2) // 2 + 1, y0 + 2, z1 - 1, "north", ["", "GENERAL", "STORE"], SHELL[pack]["wood"])




def dovecote(d, x, z, pack):
    """Square stone dovecote with nest holes and a pyramid cap."""
    y0 = d.gy + 1
    wall = {"Hearthwood": "smooth_sandstone", "Cascadia": "spruce_planks", "Neoterra": "white_concrete"}[pack]
    for y in range(y0, y0 + 6):
        for ax, az in cells(x, z, x + 4, z + 4):
            if ax in (x, x + 4) or az in (z, z + 4):
                d.set(ax, y, az, wall if (y < y0 + 4 or (ax + az + y) % 2) else
                      trap("spruce" if pack != "Neoterra" else "birch", "north", "top"))
    d.door(x + 2, y0, z, "south", SHELL[pack]["wood"])
    rb = {"Hearthwood": "mud_brick", "Cascadia": "dark_oak", "Neoterra": "smooth_quartz"}[pack]
    _spire(d, x + 1, z + 1, x + 3, z + 3, y0 + 6, rb)


def aframe_hut(d, x1, z1, bedc, v=0):
    """Small guest A-frame (9 wide, door to the north); v picks one of four hand-made interiors."""
    y0 = d.gy + 1
    x2, z2 = x1 + 8, z1 + 7
    for x, z in cells(x1, z1, x2, z2):
        d.set(x, d.gy, z, "spruce_planks" if x1 < x < x2 and z1 < z < z2 else "cobblestone")
    aframe(d, x1, x2, z1, z2, y0, "mangrove", "mangrove_planks")
    for x in range(x1 + 1, x2):
        j = min(x - x1, x2 - x)
        for y in range(y0, y0 + 2 * j):
            d.set(x, y, z1, "glass_pane" if x != x1 + 4 else log("stripped_spruce_log", "y"))
            d.set(x, y, z2, "spruce_planks")
    d.door(x1 + 4, y0, z1, "south", "spruce")
    d.set(x1 + 4, y0 + 2, z1, log("stripped_spruce_log", "x"))
    for x in range(x1 - 1, x2 + 2):                       # little deck
        d.set(x, d.gy, z1 - 1, "spruce_planks")
    d.set(x1 + 4, y0 + 5, z1 + 3, CHAIN)
    d.set(x1 + 4, y0 + 4, z1 + 3, LANT)
    flue = "cobblestone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]"

    def stove(x, z, f):
        d.set(x, y0, z, f"smoker[facing={f},lit=true]")
        for y in range(y0 + 1, y0 + 12):
            if d.air(x, y, z):
                d.set(x, y, z, flue)
    X, Z = x1, z1
    if v == 0:      # reading hut: bed at the back left, stove back right, armchair by the glass
        d.bed(X + 2, y0, Z + 6, "south", bedc)
        stove(X + 6, Z + 6, "north")
        fit(d, [(X + 2, y0, Z + 4, CHEST("north")), (X + 6, y0, Z + 2, stair("spruce", "north")),
                (X + 5, y0, Z + 2, "potted_fern")])
        rugc(d, X + 3, Z + 2, X + 5, Z + 4, y0, "red")
    elif v == 1:    # painter's hut: bed back right, stove left, easel and chest by the glass
        d.bed(X + 6, y0, Z + 6, "south", bedc)
        stove(X + 2, Z + 6, "north")
        fit(d, [(X + 2, y0, Z + 2, fence("spruce")),
                (X + 2, y0 + 1, Z + 2, "spruce_trapdoor[facing=south,half=top,open=true,powered=false,waterlogged=false]"),
                (X + 3, y0, Z + 3, stair("spruce", "north")), (X + 6, y0, Z + 4, CHEST("west")),
                (X + 6, y0, Z + 2, "bookshelf")])
        rugc(d, X + 3, Z + 4, X + 5, Z + 5, y0, "orange")
    elif v == 2:    # family hut: two beds side by side, stove at the front, table for two
        d.bed(X + 3, y0, Z + 6, "south", bedc)
        d.bed(X + 5, y0, Z + 6, "south", bedc)
        stove(X + 6, Z + 2, "west")
        fit(d, [(X + 4, y0, Z + 6, slab("spruce", "top")), (X + 4, y0 + 1, Z + 6, "candle[candles=1,lit=false,waterlogged=false]"),
                (X + 3, y0, Z + 3, slab("spruce", "top")), (X + 2, y0, Z + 3, stair("spruce", "west")),
                (X + 3, y0, Z + 2, stair("spruce", "north"))])
    else:           # angler's hut: bed along the side, tackle barrels and a rod rack
        d.bed(X + 2, y0, Z + 5, "south", bedc)
        stove(X + 6, Z + 6, "west")
        fit(d, [(X + 2, y0, Z + 2, BRL("east")), (X + 6, y0, Z + 3, BRL("west")), (X + 6, y0, Z + 2, fence("spruce")),
                (X + 6, y0 + 1, Z + 2, fence("spruce")), (X + 4, y0, Z + 6, stair("spruce", "south")),
                (X + 2, y0, Z + 6, "potted_fern")])
        rugc(d, X + 3, Z + 3, X + 5, Z + 4, y0, "light_blue")

# ============================================================================================ HOUSE estates
def house_estate_hw(rel, L):
    """Tudor farmstead: the family house (red-tile roof) grows a well and kitchen garden, a barn (brown tile)
    and stable round a farmyard, a dower house (pink wash, blue slate) and greenhouse, finally a workshop,
    bakehouse, great tithe barn (shingles), orchard and duck pond."""
    d = Design("Hearthwood", rel, (56, 40, 62), paving="grass_block[snowy=false]")
    main = house_hw(rel, 1 if L == 1 else 5)
    recolor(main, [("deepslate_tile", "brick")], parts=("full", "stairs", "slab"))
    stamp(d, main, 0, 0, primary=True)
    if L >= 2:
        lane(d, 22, 0, 24, 30, "gravel", "cobblestone")
        well(d, 27, 3, "Hearthwood")
        garden(d, 26, 7, 33, 13, 2, "spruce", ((26, 10, "west"),), beds=False)
        for z, crop in ((8, "carrots[age=7]"), (9, "potatoes[age=7]"), (11, "beetroots[age=3]"),
                        (12, "carrots[age=7]")):                                  # kitchen-garden rows
            for x in range(27, 33):
                fit(d, [(x, 1, z, "farmland[moisture=7]"), (x, 2, z, crop)])
        fit(d, [(x, 1, 10, "dirt_path") for x in range(27, 33)])
        lamp_post(d, 21, 1, 1)
        bench(d, 29, 1, 2, "east", "north", "dark_oak")
    if L >= 3:
        lane(d, 25, 14, 55, 16, "gravel")
        outbuilding(d, 35, 3, 49, 12, "barn", h=5)
        fit(d, [  # barn: hay stack back-left, feed barrels back-right, tool corner by the door, lights
            (36, 2, 11, HAYX), (37, 2, 11, HAYX), (38, 2, 11, HAYX), (36, 2, 10, HAYX), (37, 2, 10, HAYX),
            (36, 3, 11, HAYZ), (37, 3, 11, HAYZ), (36, 4, 11, HAYX),
            (48, 2, 11, BRL()), (47, 2, 11, BRL("north")), (48, 2, 10, "composter[level=4]"),
            (48, 2, 6, BRL("west")), (36, 2, 4, CHEST("east")), (36, 2, 5, GRIND("east")),
            (38, 6, 7, LANT), (45, 6, 7, LANT)])
        wagon(d, 43, 8, 2, "dark_oak")
        recolor(d, [("deepslate_tile", "mud_brick")], (34, 2, 50, 13))
        for x in range(35, 50):
            d.set(x, 1, 13, "gravel")
        outbuilding(d, 40, 18, 52, 25, "stable", h=4)
        fit(d, [(x, 2, 22, fence("dark_oak")) for x in (41, 43, 44, 45, 47, 48, 49, 51)]      # box fronts
            + [(42, 2, 22, gate("dark_oak", "north")), (46, 2, 22, gate("dark_oak", "north")),
               (50, 2, 22, gate("dark_oak", "north"))]
            + [(x, 2, z, fence("dark_oak")) for x in (44, 48) for z in (23, 24)]        # box partitions
            + [(41, 2, 24, HAYY), (43, 2, 24, CAUL), (45, 2, 24, HAYY), (47, 2, 24, CAUL),
               (49, 2, 24, CAUL), (51, 2, 24, HAYY),
               (51, 2, 19, BRL("west")), (51, 2, 20, HAYY), (41, 2, 19, CHEST("east")),
               (51, 4, 21, "brown_wall_banner[facing=west]"), (43, 5, 21, LANT), (49, 5, 21, LANT)])
        for x in range(40, 53):
            d.set(x, 1, 17, "gravel")
        lamp_post(d, 34, 14, 1)
        wagon(d, 29, 15, 2, "dark_oak")
    if L >= 4:
        dower = house_hw(rel, 1, v=1)
        recolor(dower, [("deepslate_tile", "dark_prismarine"), ("calcite", "pink_terracotta")],
                parts=("full", "stairs", "slab"))
        stamp(d, dower, 26, 27)
        outbuilding(d, 2, 28, 12, 35, "greenhouse", h=3)
        for z, crop in ((30, "carrots[age=7]"), (31, "beetroots[age=3]"), (33, "potatoes[age=7]"),
                        (34, "wheat[age=7]")):                                    # four bed rows
            for x in (3, 4, 5, 6, 8, 9, 10, 11):
                fit(d, [(x, 1, z, "farmland[moisture=7]"), (x, 2, z, crop)])
        fit(d, [(7, 1, z, "gravel") for z in range(29, 35)]
            + [(7, 2, 34, CAUL), (3, 2, 29, "potted_red_tulip"), (11, 2, 29, "potted_fern")])
        lane(d, 7, 25, 8, 27, "gravel")
        lamp_post(d, 24, 26, 1)
        for tx, tz in ((15, 30), (20, 33), (16, 37)):              # three old apple trees
            tree(d, tx, tz, 2, "oak", 4, 2)
    if L >= 5:
        outbuilding(d, 2, 40, 14, 48, "workshop", h=4)
        fit(d, [  # carpenter: bench on the back wall, timber stock, sawhorse table, chest and barrel by the door
            (4, 2, 47, "crafting_table"), (5, 2, 47, slab("dark_oak", "top")), (5, 3, 47, POT), (6, 2, 47, slab("dark_oak", "top")),
            (6, 3, 47, "candle[candles=2,lit=false,waterlogged=false]"), (11, 2, 47, "smithing_table"),
            (12, 2, 47, BRL("north")), (13, 2, 47, GRIND("west")),
            (13, 2, 42, log("stripped_oak_log", "z")), (13, 2, 43, log("stripped_oak_log", "z")),
            (13, 3, 42, log("stripped_oak_log", "z")), (3, 2, 41, CHEST("east")), (3, 2, 42, BRL("east")),
            (8, 2, 45, slab("dark_oak", "top")), (9, 2, 45, slab("dark_oak", "top")), (8, 2, 44, stair("dark_oak", "north")),
            (5, 5, 44, LANT), (11, 5, 44, LANT)])
        recolor(d, [("deepslate_tile", "granite"), ("calcite", "yellow_terracotta")], (1, 39, 15, 49))
        outbuilding(d, 16, 42, 23, 48, "bakehouse", h=4)
        fit(d, [(18, 2, 47, "bricks"), (19, 2, 47, "smoker[facing=north,lit=true]"), (20, 2, 47, "bricks"),
                (18, 3, 47, "bricks"), (19, 3, 47, "bricks"), (20, 3, 47, "bricks"),           # bread oven
                (21, 2, 44, slab("dark_oak", "top")), (17, 2, 43, BRL("east")), (17, 3, 43, "white_wool"),
                (22, 2, 43, "white_wool"), (22, 2, 46, slab("dark_oak", "top")), (22, 3, 46, POT), (19, 5, 45, LANT)]
            + [(19, y, 48, "bricks") for y in range(4, 11)])                                  # oven flue
        pond(d, 48, 29, 54, 35)
        for tx, tz in ((50, 41), (53, 45), (49, 47)):              # birches by the pond
            tree(d, tx, tz, 2, "birch", 5, 2)
        lane(d, 2, 37, 23, 39, "gravel")
        for x in (6, 19):
            bench(d, x, 38, 2, "east", "south", "dark_oak")
        outbuilding(d, 26, 51, 52, 60, "barn", h=6)
        fit(d, [(x, y, z, HAYX) for x in (27, 28, 29) for z in (58, 59) for y in (2, 3)]   # hay bays
            + [(x, y, 59, HAYZ) for x in (33, 34, 35) for y in (2, 3)]
            + [(47, 2, 59, "white_wool"), (48, 2, 59, "white_wool"), (48, 2, 58, "white_wool"),
               (47, 3, 59, "white_wool"), (50, 2, 59, BRL()), (51, 2, 59, BRL("north")),
               (27, 2, 52, CHEST("east")), (36, 2, 56, "composter[level=7]"),
               (31, 7, 55, LANT), (39, 7, 55, LANT), (47, 7, 55, LANT)])
        wagon(d, 40, 56, 2, "dark_oak")
        recolor(d, [("deepslate_tile", "dark_oak")], (25, 50, 53, 61))
        lane(d, 24, 49, 53, 50, "gravel")
        lane(d, 24, 17, 25, 50, "gravel")
        for x in (30, 48):
            lamp_post(d, x, 49, 1)
    return d


def house_estate_ca(rel, L):
    """Homestead ranch: the log home (dark shake roof), then woodshed and well, a red log barn (slate roof) with
    a corral, birch-sided bunk cabins and a smokehouse, finally a stable (blue-green metal roof), a stone silo,
    pond, garden and spruce stands."""
    d = Design("Cascadia", rel, (60, 40, 58), paving="grass_block[snowy=false]")
    main = house_ca(rel, 1 if L == 1 else 5)
    recolor(main, [("dark_oak", "cobbled_deepslate")])
    stamp(d, main, 0, 0, primary=True)
    if L >= 2:
        outbuilding(d, 28, 3, 35, 8, "shed", h=3)
        fit(d, [(x, y, 7, log("spruce_log", "x")) for x in (29, 30, 31) for y in (2, 3)]    # cordwood
            + [(33, 2, 6, log("stripped_spruce_log", "y")), (34, 2, 7, BRL("north")), (29, 2, 4, BRL("east")),
               (34, 2, 4, CHEST("west")), (32, 4, 5, LANT)])
        well(d, 26, 12, "Cascadia")
        lane(d, 24, 0, 26, 9, "coarse_dirt")
        lamp_post(d, 27, 1, 1, "ca")
        for x in range(36, 42):
            d.set(x, 2, 6, log("spruce_log", "x"))
            if x % 2:
                d.set(x, 3, 6, log("spruce_log", "x"))
    if L >= 3:
        lane(d, 24, 14, 46, 15, "coarse_dirt")
        outbuilding(d, 28, 17, 44, 27, "barn", h=5)
        fit(d, [(x, 2, z, HAYX) for x in (29, 30, 31) for z in (25, 26)]
            + [(29, 3, 26, HAYZ), (30, 3, 26, HAYZ), (43, 2, 26, BRL()), (42, 2, 26, BRL("north")),
               (43, 2, 25, "composter[level=5]"), (29, 2, 18, CHEST("east")), (29, 2, 19, GRIND("east")),
               (43, 2, 19, fence("spruce")), (43, 2, 20, fence("spruce")), (32, 6, 22, LANT), (40, 6, 22, LANT)])
        wagon(d, 38, 22, 2, "spruce")
        recolor(d, [("spruce_planks", "mangrove_planks"), ("dark_oak", "deepslate_tile")], (27, 16, 45, 28, 3),
                parts=("stairs", "slab"))
        for x, z in cells(47, 6, 58, 27):
            if x in (47, 58) or z in (6, 27):
                d.set(x, 2, z, fence("spruce"))
            else:
                d.set(x, 1, z, "coarse_dirt" if (x + z) % 3 else "grass_block[snowy=false]")
        d.set(47, 2, 15, gate("spruce", "east"))
        for z in (8, 9):
            d.set(57, 2, z, "hay_block[axis=y]")
        d.set(57, 2, 11, "water_cauldron[level=3]")
        d.set(57, 2, 12, "water_cauldron[level=3]")
    if L >= 4:
        lane(d, 0, 26, 26, 27, "coarse_dirt")
        cabin(d, 1, 31, "south", True, 2, "lime", extra_barrel=False, layout=BUNKS[0])
        cabin(d, 13, 31, "south", False, 2, "orange", extra_barrel=False, layout=BUNKS[1])
        recolor(d, [("stripped_spruce_log", "stripped_birch_log"), ("dark_oak", "mangrove")], (0, 28, 24, 42))
        outbuilding(d, 30, 31, 37, 37, "bakehouse", h=3)
        fit(d, [(32, 2, 36, "smoker[facing=north,lit=true]"), (35, 2, 36, "smoker[facing=north,lit=true]"),
                (31, 2, 36, BRL("north")), (36, 2, 36, BRL("north")), (35, 2, 33, slab("spruce", "top")),
                (33, 4, 35, CHAIN), (34, 4, 35, CHAIN), (33, 4, 33, LANT)]                       # smokehouse
            + [(34, y, 37, "cobblestone") for y in range(4, 9)])
        lamp_post(d, 12, 28, 1, "ca")
        outbuilding(d, 48, 45, 56, 51, "shed", h=3)
        fit(d, [(53, 2, 50, HAYY), (54, 2, 50, HAYY), (55, 2, 50, HAYY),                     # hen house
                (49, 2, 49, fence("spruce")), (50, 2, 49, fence("spruce")), (49, 2, 50, BRL("north")),
                (49, 2, 46, "composter[level=3]"), (55, 2, 46, CHEST("west")), (52, 4, 48, LANT)])
        garden(d, 38, 44, 46, 51, 2, "spruce", ((42, 44, "north"),), beds=False)
        for x, crop in ((39, "potatoes[age=7]"), (40, "potatoes[age=7]"), (41, "carrots[age=7]"),
                        (43, "beetroots[age=3]"), (44, "carrots[age=7]"), (45, "potatoes[age=7]")):
            for z in range(45, 51):                                                     # garden rows
                fit(d, [(x, 1, z, "farmland[moisture=7]"), (x, 2, z, crop)])
    if L >= 5:
        outbuilding(d, 40, 31, 56, 40, "stable", h=4)
        fit(d, [(x, 2, 37, fence("spruce")) for x in range(41, 56) if x not in (43, 48, 53)]
            + [(43, 2, 37, gate("spruce", "north")), (48, 2, 37, gate("spruce", "north")),
               (53, 2, 37, gate("spruce", "north"))]
            + [(x, 2, z, fence("spruce")) for x in (45, 50) for z in (38, 39)]
            + [(41, 2, 39, HAYY), (44, 2, 39, CAUL), (46, 2, 39, HAYY), (49, 2, 39, CAUL), (51, 2, 39, HAYY),
               (55, 2, 39, CAUL), (55, 2, 32, BRL("west")), (55, 2, 33, CHEST("west")), (41, 2, 32, HAYY),
               (41, 4, 34, "green_wall_banner[facing=east]"), (44, 5, 35, LANT), (52, 5, 35, LANT)])
        recolor(d, [("dark_oak", "dark_prismarine")], (39, 30, 57, 41))
        cx, cz = 25, 22
        for y in range(2, 14):
            for ax, az in cells(cx - 2, cz - 2, cx + 2, cz + 2):
                if (abs(ax - cx) == 2 or abs(az - cz) == 2) and not (abs(ax - cx) == 2 and abs(az - cz) == 2):
                    d.set(ax, y, az, "cobblestone" if y < 4 else ("stripped_spruce_log[axis=y]" if (ax + az) % 2
                                                               else "spruce_planks"))
        for ax, az in cells(cx - 1, cz - 1, cx + 1, cz + 1):
            d.set(ax, 14, az, "dark_oak_planks")
        d.set(cx, 15, cz, "dark_oak_slab[type=bottom,waterlogged=false]")
        for ax, az, f in ((cx - 2, cz, "east"), (cx + 2, cz, "west"), (cx, cz - 2, "south"), (cx, cz + 2, "north")):
            d.set(ax, 14, az, stair("dark_oak", f))
        pond(d, 2, 44, 10, 50)
        for tx, tz in ((14, 45), (19, 48), (24, 44), (28, 49), (16, 53), (23, 54), (29, 55)):   # spruce stand
            tree(d, tx, tz, 2, "spruce", 6, 2)
        lane(d, 38, 28, 39, 41, "coarse_dirt")
        bench(d, 4, 41, 2, "east", "north", "spruce")
        wagon(d, 41, 28, 2, "spruce")
        for x, z in ((27, 40), (37, 41), (20, 29), (46, 29)):
            lamp_post(d, x, z, 1, "ca")
        bench(d, 20, 41, 2, "east", "north", "spruce")
        for z in range(44, 56, 3):
            d.set(57, 2, z, "hay_block[axis=y]")
        for z in range(42, 56):
            d.set(36, 2, z, fence("spruce"))
        for x in range(48, 56):                           # cordwood stacked by the stable
            d.set(x, 2, 42, log("spruce_log", "x"))
            d.set(x, 3, 42, log("spruce_log", "x"))
        outbuilding(d, 44, 49, 57, 57, "garage", h=4)      # implement shed: sled, plough, saw bench
        recolor(d, [("dark_oak", "mangrove")], (43, 48, 58, 58))
        wagon(d, 46, 54, 2, "spruce", log("spruce_log", "x"))
        fit(d, [(56, 2, 56, GRIND("west")), (55, 2, 56, slab("spruce", "top")), (54, 2, 56, slab("spruce", "top")),
                (54, 3, 56, LANTF), (45, 2, 56, CHEST("north")), (56, 2, 52, "anvil[facing=north]"),
                (56, 2, 50, BRL("west")), (45, 2, 50, HAYY), (48, 5, 52, LANT), (53, 5, 52, LANT)])
    return d


def house_estate_nt(rel, L):
    """Modern compound: the villa (orange accents), then a lit drive, a pool with pool house and a studio,
    guest villas in grey and terracotta with a garage, finally a greenhouse, fitness pavilion and two more
    guest villas on a birch-lined walk."""
    d = Design("Neoterra", rel, (56, 40, 64), paving="grass_block[snowy=false]")
    main = house_nt(rel, 1 if L == 1 else 5)
    recolor(main, [("cyan_terracotta", "orange_terracotta")])
    stamp(d, main, 0, 0, primary=True)
    if L >= 2:
        lane(d, 21, 0, 23, 22, "smooth_stone", "polished_andesite")
        for z in (2, 8, 14, 20):
            lamp_post(d, 24, z, 1, "nt")
        planter(d, 25, 1, 33, 1, 1)
    if L >= 3:
        for x, z in cells(26, 4, 42, 13):
            d.set(x, 1, z, "smooth_quartz")
        for x, z in cells(28, 6, 38, 11):
            d.set(x, 1, z, "water")
            d.set(x, 0, z, "light_blue_concrete")
        for x in (29, 32, 35):
            d.chair(x, 2, 12, "south", "birch", sit=False)
        outbuilding(d, 44, 3, 52, 12, "poolhouse", h=3)
        sofa(d, 45, 11, 2, 3, "east", "south", "birch", arms=False, sit=False)
        fit(d, [(48, 2, 11, slab("smooth_quartz", "top")), (48, 3, 11, "potted_bamboo"), (51, 2, 11, "potted_bamboo"),
                (51, 2, 4, CHEST("west")), (51, 2, 5, "white_wool"), (51, 2, 7, slab("smooth_quartz", "top")),
                (51, 2, 8, slab("smooth_quartz", "top")), (50, 2, 7, stair("birch", "west")),
                (50, 2, 8, stair("birch", "west")), (45, 2, 10, "light_blue_carpet"), (46, 2, 10, "light_blue_carpet"),
                (47, 2, 10, "light_blue_carpet"), (45, 2, 4, CAUL), (45, 2, 5, "potted_fern")])
        outbuilding(d, 26, 17, 38, 24, "workshop", h=4)
        easel = "birch_trapdoor[facing=south,half=top,open=true,powered=false,waterlogged=false]"
        fit(d, [(28, 2, 22, fence("birch")), (28, 3, 22, easel), (30, 2, 22, fence("birch")), (30, 3, 22, easel),
                (36, 2, 22, slab("smooth_quartz", "top")), (37, 2, 22, slab("smooth_quartz", "top")),
                (36, 2, 21, stair("birch", "north")), (27, 2, 18, "bookshelf"), (27, 3, 18, "potted_fern"),
                (37, 2, 18, "loom[facing=west]"), (37, 2, 19, "cartography_table"), (33, 2, 23, BRL("north")),
                (34, 2, 23, POT), (29, 6, 20, "sea_lantern"), (35, 6, 20, "sea_lantern")])          # art studio
        rugc(d, 29, 19, 31, 20, 2, "orange")
        recolor(d, [("white_concrete", "orange_terracotta")], (26, 17, 38, 24, 2))
    if L >= 4:
        g = house_nt(rel, 1, v=1)
        recolor(g, [("white_concrete", "light_gray_concrete"), ("cyan_terracotta", "yellow_terracotta"),
                    ("stripped_birch_log", "stripped_mangrove_log")])
        stamp(d, g, 0, 25)
        outbuilding(d, 41, 17, 53, 25, "garage", h=4)
        wagon(d, 46, 21, 2, "birch", CHEST("north"))                                         # estate cart
        fit(d, [(43, 2, 24, CHEST("north")), (44, 2, 24, slab("birch", "top")), (45, 2, 24, slab("birch", "top")),
                (45, 3, 24, LANTF), (51, 2, 24, BRL("north")), (52, 2, 24, "anvil[facing=east]"),
                (42, 2, 19, GRIND("east")), (44, 6, 21, "sea_lantern"), (50, 6, 21, "sea_lantern")])
        lane(d, 41, 26, 53, 27, "smooth_stone")
    if L >= 5:
        outbuilding(d, 26, 30, 38, 38, "greenhouse", h=4)
        for z, crop in ((32, "carrots[age=7]"), (33, "beetroots[age=3]"), (35, "potatoes[age=7]"),
                        (36, "wheat[age=7]")):
            for x in (27, 28, 29, 30, 31, 33, 34, 35, 36, 37):
                fit(d, [(x, 1, z, "farmland[moisture=7]"), (x, 2, z, crop)])
        fit(d, [(32, 1, z, "gravel") for z in range(31, 38)]
            + [(32, 2, 37, CAUL), (27, 2, 31, "potted_bamboo"), (37, 2, 31, "potted_flowering_azalea_bush")])
        outbuilding(d, 41, 30, 53, 40, "workshop", h=4)
        fit(d, [(42, 2, 32, CHEST("east")), (42, 2, 33, CHEST("east")), (42, 2, 34, CHEST("east")),   # gym
                (45, 2, 38, stair("birch", "south")), (46, 2, 38, "anvil[facing=east]"),
                (50, 5, 35, CHAIN), (50, 4, 35, CHAIN), (50, 3, 35, "white_wool"),
                (52, 2, 39, CAUL), (52, 2, 31, "potted_bamboo"), (44, 6, 35, "sea_lantern"),
                (50, 6, 37, "sea_lantern")])
        rugc(d, 44, 35, 48, 36, 2, "light_gray")
        recolor(d, [("white_concrete", "polished_deepslate")], (41, 30, 53, 40, 2))
        planter(d, 26, 42, 53, 42, 1)
        for x in (28, 36, 44, 52):
            tree(d, x, 45, 2, "birch", 5, 2)
        lane(d, 22, 28, 55, 29, "smooth_stone")
        for gx, pal in ((0, [("white_concrete", "white_terracotta"), ("cyan_terracotta", "lime_terracotta")]),
                        (26, [("white_concrete", "light_gray_concrete"), ("cyan_terracotta", "magenta_terracotta"),
                              ("stripped_birch_log", "stripped_cherry_log")])):
            g = house_nt(rel, 1, v=2 if gx == 0 else 3)
            recolor(g, pal)
            stamp(d, g, gx, 48)
        lane(d, 0, 46, 55, 47, "smooth_stone")
    return d


# ============================================================================================ COTTAGE hamlets
def cottage_hamlet_hw(rel, L):
    """Cotswold smallholding (honey stone, brown-tile roof): the cottage, then a well, potting shed and bee
    garden, a cart shed and pigsty, a dovecote and orchard, finally the neighbour's cottage (slate), a cider
    barn and duck pond – a little hamlet."""
    d = Design("Hearthwood", rel, (58, 40, 54), paving="grass_block[snowy=false]")
    main = cottage_hw(rel, L)
    recolor(main, [("deepslate_tile", "mud_brick")], parts=("full", "stairs", "slab"))
    stamp(d, main, 0, 0, primary=True)
    if L >= 2:
        well(d, 24, 4, "Hearthwood")
        addon(d, 22, 9, 29, 14, "potting")
        fit(d, [(23, 2, 13, "composter[level=6]"), (28, 2, 13, BRL("west")), (28, 2, 10, CAUL),   # potting shed
                (23, 2, 10, "potted_fern"), (26, 4, 11, LANT)]
            + [(x, 2, 13, slab("spruce", "top")) for x in (24, 25, 26, 27)]
            + [(24, 3, 13, "potted_red_tulip"), (25, 3, 13, "flower_pot"), (26, 3, 13, "potted_cornflower"),
               (27, 3, 13, POT)])
        recolor(d, [("deepslate_tile", "brick"), ("calcite", "smooth_sandstone")], (21, 8, 30, 15))
        lane(d, 20, 0, 21, 16, "gravel")
        lamp_post(d, 19, 1, 1)
        bench(d, 26, 2, 2, "east", "north", "dark_oak")
        # bee garden: hives on posts among lavender-ish flowers
        garden(d, 46, 2, 57, 11, 2, "spruce", ((51, 11, "south"),),
               plants=((47, 3, "allium"), (49, 3, "cornflower"), (50, 4, "lilac[half=lower]"), (52, 3, "oxeye_daisy"),
                       (53, 4, "allium"), (55, 3, "cornflower"), (56, 4, "lilac[half=lower]"),
                       (47, 6, "oxeye_daisy"), (49, 7, "allium"), (50, 6, "cornflower"), (52, 7, "lilac[half=lower]"),
                       (53, 6, "oxeye_daisy"), (55, 7, "allium"), (56, 6, "cornflower"), (47, 9, "lilac[half=lower]"),
                       (49, 10, "cornflower"), (53, 10, "allium"), (55, 9, "oxeye_daisy")))
        for x in (48, 51, 54):
            for z in (5, 8):
                d.set(x, 2, z, fence("spruce"))
                d.set(x, 3, z, "beehive[facing=south,honey_level=3]")
                d.set(x, 4, z, AIR)
    if L >= 3:
        addon(d, 31, 3, 44, 11, "cartshed", h=4)
        wagon(d, 34, 7, 2, "dark_oak")
        fit(d, [(43, 2, 10, GRIND("west")), (42, 2, 10, BRL("north")), (32, 2, 10, HAYY), (33, 2, 10, CHEST("north")),
                (40, 2, 10, fence("dark_oak")), (40, 3, 10, LANTF), (38, 5, 7, LANT)])
        recolor(d, [("deepslate_tile", "dark_oak"), ("calcite", "smooth_sandstone")], (30, 2, 45, 12))
        # pigsty: low stone walls, a mud yard, a trough and a lean-to
        for x, z in cells(1, 24, 10, 30):
            if x in (1, 10) or z in (24, 30):
                d.set(x, 2, z, "cobblestone_wall[east=low,north=low,south=low,up=true,waterlogged=false,west=low]")
            else:
                d.set(x, 1, z, "mud" if (x + z) % 3 else "coarse_dirt")
        d.set(5, 2, 24, gate("spruce", "north"))
        d.set(8, 2, 28, "water_cauldron[level=3]")
        for x in range(2, 10):
            d.set(x, 4, 29, stair("mud_brick", "south"))
        for x in (2, 9):
            d.set(x, 2, 29, fence("spruce"))
            d.set(x, 3, 29, fence("spruce"))
        d.set(4, 2, 29, "hay_block[axis=x]")
        lane(d, 22, 15, 57, 16, "gravel")
        lamp_post(d, 30, 14, 1)
        garden(d, 11, 24, 18, 30, 2, "spruce", ((14, 24, "north"),))
        for z, crop in ((26, "carrots[age=7]"), (28, "potatoes[age=7]")):           # two vegetable rows
            for x in (12, 13, 15, 16, 17):
                d.set(x, 1, z, "farmland[moisture=7]")
                d.set(x, 2, z, crop)
        bench(d, 33, 13, 2, "east", "north", "dark_oak")
        tree(d, 52, 13, 2, "oak", 4, 2)
    if L >= 4:
        dovecote(d, 34, 19, "Hearthwood")
        for tx, tz in ((48, 21), (52, 21), (55, 25), (48, 26), (52, 28)):  # apple orchard
            tree(d, tx, tz, 2, "oak", 4, 2)
        hedge(d, 45, 18, 57, 30, "oak", gaps=((45, 24),))
        addon(d, 22, 19, 30, 26, "potting")
        fit(d, [(23, 2, 25, BRL("north")), (24, 2, 25, BRL("north")), (24, 3, 25, BRL()),         # cider house
                (27, 2, 25, "composter[level=8]"), (27, 3, 25, slab("dark_oak")), (28, 2, 25, BRL("north")),
                (29, 2, 25, BRL("north")), (29, 2, 21, CHEST("west")), (23, 2, 21, BRL("east")),
                (28, 2, 22, slab("dark_oak", "top")), (28, 3, 22, POT), (26, 4, 23, LANT)])
        recolor(d, [("deepslate_tile", "granite")], (21, 18, 31, 27))
    if L >= 5:
        nb = cottage_hw(rel, 3, v=1)
        recolor(nb, [("smooth_sandstone", "calcite"), ("cut_sandstone", "stone_bricks")])
        stamp(d, nb, 0, 32)
        addon(d, 22, 33, 33, 40, "cartshed", h=4)
        wagon(d, 25, 37, 2, "dark_oak", HAYX)                                               # hay wain
        fit(d, [(32, 2, 39, HAYY), (31, 2, 39, HAYY), (32, 3, 39, HAYY), (23, 2, 39, CHEST("north")),
                (24, 2, 39, GRIND("north")), (30, 2, 39, fence("dark_oak")), (29, 2, 39, fence("dark_oak")),
                (28, 5, 36, LANT)])
        recolor(d, [("deepslate_tile", "brick")], (21, 32, 34, 41))
        pond(d, 36, 32, 44, 38)
        dovecote(d, 48, 34, "Hearthwood")
        lane(d, 20, 17, 21, 52, "gravel")
        for z in (22, 34, 46):
            lamp_post(d, 19, z, 1)
        for tx, tz in ((25, 46), (33, 49), (41, 46), (49, 49)):
            tree(d, tx, tz, 2, "oak", 4, 2)
    return d


def cottage_retreat_ca(rel, L):
    """Mountain retreat (red-cedar A-frame): a sauna and wood store by the deck, then guest A-frames, a pond with a
    plank dock and a lookout tower, finally a second lodge A-frame, more huts and a bee garden."""
    d = Design("Cascadia", rel, (60, 40, 62), paving="grass_block[snowy=false]")
    main = cottage_ca(rel, L)
    recolor(main, [("dark_oak", "mangrove")], parts=("full", "stairs", "slab"))
    stamp(d, main, 0, 0, primary=True)
    if L >= 2:
        addon(d, 25, 3, 32, 8, "cartshed", h=3)
        fit(d, [(27, 2, 6, fence("spruce")), (30, 2, 6, fence("spruce"))]                     # canoe shed
            + [(x, 3, 6, slab("spruce")) for x in (27, 28, 29, 30)]
            + [(31, 2, 7, fence("spruce")), (31, 3, 7, fence("spruce")), (26, 2, 7, BRL("north")), (28, 4, 4, LANT)])
        addon(d, 25, 11, 32, 17, "sauna")
        fit(d, [(31, 2, 16, "smoker[facing=west,lit=true]"),                                  # sauna
                (31, 3, 16, "cobblestone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]"),
                (26, 2, 16, stair("spruce", "south")), (27, 2, 16, stair("spruce", "south")),
                (28, 2, 16, stair("spruce", "south")), (26, 2, 12, CAUL), (27, 2, 12, BRL()),
                (31, 2, 12, "white_wool"), (29, 4, 14, LANT)])
        recolor(d, [("dark_oak", "cobbled_deepslate")], (24, 2, 33, 18))
        lane(d, 22, 0, 23, 20, "coarse_dirt")
        lamp_post(d, 24, 1, 1, "ca")
        for x in range(33, 37):
            d.set(x, 2, 5, log("spruce_log", "x"))
            d.set(x, 3, 5, log("spruce_log", "x"))
    if L >= 3:
        aframe_hut(d, 36, 3, "lime")
        aframe_hut(d, 48, 3, "orange", 1)
        lane(d, 24, 19, 59, 20, "coarse_dirt")
        lamp_post(d, 46, 18, 1, "ca")
        lamp_post(d, 34, 18, 1, "ca")
        bench(d, 38, 18, 2, "east", "north", "spruce")
        for x in range(44, 48):                              # firewood stack between the huts
            d.set(x, 2, 1, log("spruce_log", "x"))
            d.set(x, 3, 1, log("spruce_log", "x"))
        lamp_post(d, 58, 18, 1, "ca")
        bench(d, 50, 18, 2, "east", "north", "spruce")
        # picnic tables and a fire bowl between the huts
        for tx in (40, 52):
            d.dining(tx, 2, 15, 2, "x", "spruce", ("n", "s"), sit=False)
        d.set(46, 1, 15, "cobblestone")
        d.set(46, 2, 15, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        tree(d, 57, 31, 2, "spruce", 6, 2)
    if L >= 4:
        for tx, tz in ((3, 31), (8, 34), (13, 30), (18, 35), (5, 37)):
            tree(d, tx, tz, 2, "spruce", 6, 2)
        pond(d, 26, 24, 40, 34)
        for z in range(25, 30):                            # plank dock into the pond
            d.set(33, 1, z, "spruce_planks")
            d.set(34, 1, z, "spruce_planks")
        d.set(33, 2, 29, fence("spruce"))
        fit(d, [(23, 1, 30, "cobblestone"), (23, 2, 30, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]"),
                (21, 2, 30, log("spruce_log", "z")), (21, 2, 29, log("spruce_log", "z")),
                (25, 2, 30, log("spruce_log", "z")), (25, 2, 31, log("spruce_log", "z")),
                (23, 2, 33, log("spruce_log", "x")), (24, 2, 33, log("spruce_log", "x"))])
        lamp_post(d, 34, 23, 1, "ca")
        tree(d, 22, 27, 2, "spruce", 6, 2)
        addon(d, 42, 24, 52, 31, "workshop")
        fit(d, [(44, 2, 28, fence("spruce")), (48, 2, 28, fence("spruce"))]                    # canoe workshop
            + [(x, 3, 28, slab("spruce")) for x in (44, 45, 46, 47, 48)]
            + [(43, 2, 30, "crafting_table"), (44, 2, 30, slab("spruce", "top")), (45, 2, 30, slab("spruce", "top")),
               (45, 3, 30, POT), (50, 2, 30, BRL("north")), (51, 2, 30, CHEST("west")),
               (51, 2, 26, fence("spruce")), (51, 3, 26, fence("spruce")), (47, 4, 27, LANT)])
        for y in range(2, 11):
            for x, z in ((54, 22), (57, 22), (54, 25), (57, 25)):
                d.set(x, y, z, log("spruce_log", "y"))
        d.fill(54, 11, 22, 57, 11, 25, "spruce_planks")
        for x, z in cells(54, 22, 57, 25):
            if x in (54, 57) or z in (22, 25):
                d.set(x, 12, z, fence("spruce"))
        d.set(56, 12, 25, AIR)
        for y in range(2, 12):
            d.set(56, y, 26, "ladder[facing=south,waterlogged=false]")
            if y < 11:
                d.set(56, y, 25, "spruce_planks")
        for x, z in cells(53, 21, 58, 26):
            d.set(x, 14, z, "mangrove_slab[type=bottom,waterlogged=false]")
        for x, z in ((54, 22), (57, 22), (54, 25), (57, 25)):
            d.set(x, 13, z, log("spruce_log", "y"))
    if L >= 5:
        lodge = cottage_ca(rel, 5, v=1)
        recolor(lodge, [("dark_oak", "dark_prismarine")], parts=("full", "stairs", "slab"))
        stamp(d, lodge, 0, 35, hut_to="barrel[facing=up,open=false]")
        aframe_hut(d, 30, 40, "cyan", 2)
        aframe_hut(d, 42, 40, "pink", 3)
        lane(d, 24, 37, 59, 38, "coarse_dirt")
        for x in (29, 41, 53):
            lamp_post(d, x, 36, 1, "ca")
        addon(d, 30, 51, 42, 57, "cartshed", h=3)
        wagon(d, 33, 54, 2, "spruce", log("spruce_log", "x"))                               # wood store
        fit(d, [(x, y, 56, log("spruce_log", "x")) for x in (37, 38, 39, 40, 41) for y in (2, 3)]
            + [(31, 2, 56, CHEST("north")), (36, 4, 53, LANT)])
        garden(d, 44, 51, 57, 58, 2, "spruce", ((50, 51, "north"),),
               plants=((45, 53, "allium"), (47, 53, "cornflower"), (53, 53, "lilac[half=lower]"),
                       (56, 53, "oxeye_daisy"), (45, 57, "cornflower"), (52, 57, "allium")))
        for x in (46, 49, 52, 55):
            d.set(x, 2, 55, fence("spruce"))
            d.set(x, 3, 55, "beehive[facing=north,honey_level=2]")
        lane(d, 28, 49, 58, 50, "coarse_dirt")
    return d


def cottage_pavilions_nt(rel, L):
    """Garden pavilions: the green-roof pavilion, then a glasshouse on a lit garden walk, a second pavilion in
    cherry, a studio (terracotta) and reflecting pool with a third pavilion, finally two more pavilions and
    a tea house."""
    d = Design("Neoterra", rel, (62, 40, 58), paving="grass_block[snowy=false]")
    stamp(d, cottage_nt(rel, L), 0, 0, primary=True)
    if L >= 2:
        lane(d, 19, 0, 20, 24, "smooth_stone")
        for z in (3, 11, 19):
            lamp_post(d, 21, z, 1, "nt")
        addon(d, 24, 3, 34, 10, "teahouse", h=4)
        fit(d, [(29, 2, 7, "bamboo_slab[type=top,waterlogged=false]"),                        # tea room
                (29, 3, 7, "candle[candles=3,lit=false,waterlogged=false]"),
                (28, 2, 7, "green_carpet"), (30, 2, 7, "green_carpet"), (29, 2, 8, "green_carpet"),
                (29, 2, 6, "lime_carpet"), (25, 2, 9, "potted_bamboo"), (33, 2, 9, "potted_bamboo"),
                (25, 2, 4, "potted_azalea_bush"), (29, 4, 9, "green_wall_banner[facing=north]"),
                (31, 2, 9, slab("birch", "top")), (31, 3, 9, POT), (27, 6, 6, "sea_lantern"), (31, 6, 6, "sea_lantern")])
        recolor(d, [("white_concrete", "glass")], (24, 3, 34, 10, 3))
        planter(d, 24, 13, 34, 13, 1)
    if L >= 3:
        p2 = cottage_nt(rel, 1, v=1)
        recolor(p2, [("stripped_birch_log", "stripped_cherry_log"), ("white_concrete", "light_gray_concrete")])
        stamp(d, p2, 26, 15)
    if L >= 4:
        addon(d, 37, 3, 49, 11, "potting", h=4)
        fit(d, [(47, 2, 10, "smoker[facing=north,lit=true]"), (48, 2, 10, "bricks"), (47, 3, 10, "bricks"),   # kiln
                (48, 3, 10, "bricks"), (40, 2, 8, "stonecutter[facing=north]"), (40, 2, 7, stair("birch", "north")),
                (44, 2, 8, "stonecutter[facing=north]"), (44, 2, 7, stair("birch", "north")),   # potter's wheels
                (38, 2, 10, slab("birch", "top")), (38, 3, 10, POT), (39, 2, 10, slab("birch", "top")),
                (39, 3, 10, "flower_pot"), (40, 2, 10, slab("birch", "top")), (40, 3, 10, POT),
                (48, 2, 4, BRL("west")), (48, 2, 5, BRL("west")), (38, 2, 4, CAUL),
                (40, 6, 6, "sea_lantern"), (46, 6, 6, "sea_lantern")])
        recolor(d, [("white_concrete", "orange_terracotta")], (37, 3, 49, 11, 2))
        planter(d, 37, 13, 49, 13, 1)
        p3 = cottage_nt(rel, 3, v=2)
        recolor(p3, [("stripped_birch_log", "stripped_mangrove_log")])
        stamp(d, p3, 0, 33)
        for x, z in cells(24, 29, 45, 33):
            d.set(x, 1, z, "water" if 26 <= x <= 43 and 30 <= z <= 32 else "smooth_quartz")
        for x in (24, 45):
            tree(d, x, 35, 2, "birch", 5, 2)
        lane(d, 19, 25, 20, 57, "smooth_stone")
        for z in (30, 40, 50):
            lamp_post(d, 21, z, 1, "nt")
    if L >= 5:
        stamp(d, cottage_nt(rel, 1, v=3), 26, 38)
        p5 = cottage_nt(rel, 1, v=4)
        recolor(p5, [("stripped_birch_log", "stripped_dark_oak_log"), ("white_concrete", "white_terracotta")])
        stamp(d, p5, 44, 15)
        addon(d, 26, 51, 36, 57, "teahouse", h=3)
        fit(d, [(27, 2, 56, "bookshelf"), (28, 2, 56, "bookshelf"), (29, 2, 56, "bookshelf"),   # reading pavilion
                (33, 2, 56, "bookshelf"), (34, 2, 56, "bookshelf"), (35, 2, 56, "bookshelf"),
                (28, 2, 54, stair("birch", "south")), (34, 2, 54, stair("birch", "south")),
                (31, 2, 55, slab("birch", "top")), (31, 3, 55, "candle[candles=2,lit=false,waterlogged=false]"),
                (27, 2, 52, "potted_bamboo"), (35, 2, 52, "potted_fern"), (31, 5, 54, "sea_lantern")])
        rugc(d, 29, 53, 33, 54, 2, "light_gray")
        addon(d, 39, 51, 50, 57, "potting", h=4)
        fit(d, [(41, 2, 54, slab("birch", "top")), (42, 2, 54, slab("birch", "top")),            # plant nursery
                (41, 3, 54, "potted_fern"), (42, 3, 54, "potted_red_tulip"),
                (46, 2, 54, slab("birch", "top")), (47, 2, 54, slab("birch", "top")), (48, 2, 54, slab("birch", "top")),
                (46, 3, 54, "potted_cornflower"), (47, 3, 54, "potted_azalea_bush"), (48, 3, 54, "potted_bamboo"),
                (40, 2, 56, "composter[level=6]"), (49, 2, 56, BRL("north")), (48, 2, 56, BRL("north")),
                (40, 2, 52, CAUL), (42, 6, 55, "sea_lantern"), (47, 6, 55, "sea_lantern")])
        recolor(d, [("white_concrete", "cyan_terracotta")], (39, 51, 50, 57, 2))
        lane(d, 22, 49, 51, 50, "smooth_stone")
        for x in (52, 58):
            tree(d, x, 32, 2, "birch", 5, 2)
        for x in (24, 38, 50):
            lamp_post(d, x, 48, 1, "nt")
    return d


# ============================================================================================ QUADPLEX cabin camp
def quadplex_ca(rel, L):
    """Cabin camp: cabins (green-metal roofs, alternating birch and log walls) round a court with a fire ring,
    growing into eight cabins with a cookhouse, bathhouse, camp store and wood yard."""
    d = Design("Cascadia", rel, (62, 22, 60), paving="grass_block[snowy=false]")
    N = {1: 1, 2: 2, 3: 4, 4: 6, 5: 8}[L]
    spec = [(17, 2, "north", False, "brown"), (33, 2, "north", True, "green"),
            (17, 19, "south", True, "orange"), (33, 19, "south", False, "cyan"),
            (1, 2, "north", False, "red"), (49, 2, "north", True, "yellow"),
            (1, 19, "south", True, "purple"), (49, 19, "south", False, "lime")]
    for k in range(N):
        x1, z1, out, mir, c = spec[k]
        Wf = cabin(d, x1, z1, out, mir, 2, c, True, double=(k == 0 and L >= 5), layout=CABINS[k % 4])
        if k == 0:
            hx, hz = Wf(4, 0)
            d.hut(hx, 2, hz)
        pal = [("dark_oak", "dark_prismarine")] + ([("stripped_spruce_log", "stripped_birch_log")] if k % 2 else [])
        recolor(d, pal, (x1 - 1, z1 - 3, x1 + 9, z1 + 10))
    for x, z in cells(3, 12, 57, 16):
        d.set(x, 1, z, "coarse_dirt" if (x * 3 + z) % 4 else "gravel")
    for z in range(0, 60):
        d.set(29, 1, z, "gravel")
        d.set(30, 1, z, "gravel")
    d.set(29, 1, 14, "cobblestone")
    d.set(29, 2, 14, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for x in (28, 29, 30):
        d.set(x, 2, 12, log("spruce_log", "x"))
        d.set(x, 2, 16, log("spruce_log", "x"))
    for x in (13, 46):
        lamp_post(d, x, 14, 1, "ca")
    if L >= 4:
        addon(d, 1, 33, 26, 45, "cookhouse", h=5)
        fit(d, [(3, 2, 44, BRL("north")), (4, 2, 44, "smoker[facing=north,lit=true]"),              # cookhouse range
                (5, 2, 44, slab("spruce", "top")), (5, 3, 44, POT), (6, 2, 44, "smoker[facing=north,lit=true]"),
                (7, 2, 44, BRL("north")), (8, 2, 44, CAUL), (25, 2, 44, CHEST("west")), (25, 2, 34, BRL("west")),
                (2, 4, 40, "green_wall_banner[facing=east]"), (8, 6, 38, CHAIN), (8, 5, 38, LANT),
                (19, 6, 38, CHAIN), (19, 5, 38, LANT)])
        for x in list(range(4, 12)) + list(range(16, 24)):                                    # two long tables
            fit(d, [(x, 2, 39, slab("spruce", "top")), (x, 2, 38, stair("spruce", "north")),
                    (x, 2, 40, stair("spruce", "south"))])
        recolor(d, [("dark_oak", "mangrove")], (0, 32, 27, 46))
        addon(d, 32, 36, 42, 43, "bathhouse", h=3)
        fit(d, [(34, 2, 42, CAUL), (40, 2, 42, CAUL), (36, 2, 42, stair("spruce", "south")),        # bathhouse
                (38, 2, 42, stair("spruce", "south")), (33, 2, 37, BRL("east")), (33, 3, 37, "white_wool"),
                (41, 2, 37, CHEST("west")), (41, 2, 40, slab("spruce", "top")), (41, 3, 40, POT), (37, 4, 40, LANT)])
        lamp_post(d, 28, 32, 1, "ca")
    if L >= 5:
        px1, px2, pz1, pz2 = 44, 56, 35, 44
        addon(d, px1, pz1, px2, pz2, "store", h=4)
        fit(d, [(45, 2, 43, BRL("north")), (46, 2, 43, BRL("north")), (45, 3, 43, slab("spruce", "top")),   # store
                (46, 3, 43, slab("spruce", "top")), (47, 2, 43, CHEST("north")), (53, 2, 43, CHEST("north")),
                (54, 2, 43, BRL("north")), (55, 2, 43, BRL("north")), (54, 3, 43, slab("spruce", "top")),
                (55, 3, 43, slab("spruce", "top")), (45, 2, 36, "white_wool"), (55, 2, 36, "white_wool"),
                (48, 5, 40, LANT), (52, 5, 40, LANT)]
            + [(x, 2, 40, slab("spruce", "top")) for x in (46, 47, 48, 52, 53, 54)])            # counter
        recolor(d, [("dark_oak", "cobbled_deepslate"), ("stripped_spruce_log", "stripped_mangrove_log")],
                (px1 - 1, pz1 - 1, px2 + 1, pz2 + 1))
        d.item(px1 + 1, 2, pz1 + 3, "jukebox")
        d.item(px2 - 1, 2, pz1 + 3, "ender_chest", "west")
        for x, z in cells(30, 48, 43, 59):
            d.set(x, 1, z, "coarse_dirt" if (x + z) % 3 else "packed_mud")
        for z in (50, 53, 56):
            for x in range(32, 42):
                d.set(x, 2, z, log("spruce_log", "x"))
                if x % 3:
                    d.set(x, 3, z, log("spruce_log", "x"))
        wagon(d, 33, 58, 2, "spruce", log("spruce_log", "x"))
        addon(d, 45, 47, 58, 56, "cartshed", h=4)
        wagon(d, 48, 51, 2, "spruce", log("spruce_log", "x"))                                # tack and cart shed
        fit(d, [(56, 2, 55, fence("spruce")), (56, 3, 55, slab("spruce")), (57, 2, 55, fence("spruce")),
                (57, 3, 55, slab("spruce")), (46, 2, 55, HAYY), (47, 2, 55, HAYY), (46, 3, 55, HAYY),
                (57, 2, 49, CHEST("west")), (52, 5, 51, LANT)])
        addon(d, 2, 48, 26, 57, "bunkhouse", h=4)                                             # loggers' bunkhouse
        for x in (4, 6, 9, 11, 17, 19, 22, 24):
            d.bed(x, 2, 56, "south", "brown")
        fit(d, [(5, 2, 56, CHEST("north")), (10, 2, 56, CHEST("north")), (18, 2, 56, CHEST("north")),
                (23, 2, 56, CHEST("north")), (20, 2, 51, "smoker[facing=north,lit=true]"),
                (13, 2, 53, slab("spruce", "top")), (15, 2, 53, slab("spruce", "top")),
                (13, 2, 52, stair("spruce", "north")), (15, 2, 52, stair("spruce", "north")),
                (8, 5, 53, LANT), (20, 5, 54, LANT)])
        for y in range(3, 9):
            if d.air(20, y, 51):
                d.set(20, y, 51, "cobblestone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
        lamp_post(d, 31, 47, 1, "ca")
    return d


def finish_decor(d, base):
    """Material cap only (no placement): levels 1-3 swap premium blocks for common ones."""
    if d.level <= 3:
        common_materials(d)
    return d





# ============================================================================================ premium cap (L1-3)
COMMON = [
    # (premium id, common id) – families first, then single blocks; properties are kept
    ("smooth_quartz_stairs", "polished_diorite_stairs"), ("smooth_quartz_slab", "polished_diorite_slab"),
    ("smooth_quartz", "polished_diorite"), ("quartz_block", "calcite"), ("quartz_pillar", "calcite"),
    ("quartz_stairs", "diorite_stairs"), ("quartz_slab", "diorite_slab"),
    ("polished_blackstone_brick_wall", "deepslate_brick_wall"), ("polished_blackstone_bricks", "deepslate_bricks"),
    ("polished_blackstone_wall", "polished_deepslate_wall"), ("polished_blackstone", "polished_deepslate"),
    ("dark_prismarine_stairs", "deepslate_tile_stairs"), ("dark_prismarine_slab", "deepslate_tile_slab"),
    ("dark_prismarine", "deepslate_tiles"), ("prismarine_wall", "deepslate_tile_wall"),
    ("sea_lantern", "glowstone"),
]


def common_materials(d):
    """Levels 1-3: swap the premium bulk (quartz, blackstone, prismarine, sea lanterns, end rods) for common
    blocks – concrete/diorite/deepslate/tiles, glowstone, torches. L4-5 keep the premium look."""
    table = {"minecraft:" + a: "minecraft:" + b for a, b in COMMON}
    bp = d.bp
    for y in range(bp.sy):
        for z in range(bp.sz):
            row = bp.grid[y][z]
            for x in range(bp.sx):
                st = row[x]
                name = st.split("[")[0]
                if name in table:
                    row[x] = table[name] + st[len(name):]
                elif name == "minecraft:end_rod":
                    f = st.split("facing=")[1].split(",")[0].rstrip("]")
                    row[x] = f"minecraft:wall_torch[facing={f}]" if f in D4 else "minecraft:torch"
    return d
