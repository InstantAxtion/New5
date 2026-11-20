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


def ladder(d, x, z, y1, y2, facing):
    """Ladder from y1 to y2 (inclusive) at (x,z) facing away from its wall; clears the column."""
    for y in range(y1, y2 + 1):
        d.set(x, y, z, f"ladder[facing={facing},waterlogged=false]")


def partition(d, x1, z1, x2, z2, y1, y2, block, doors=(), wood=None):
    """Interior wall with doors [(x, z, facing)]."""
    d.fill(x1, y1, z1, x2, y2, z2, block)
    for x, z, f in doors:
        d.door(x, y1, z, f, wood)
        for yy in range(y1 + 2, y2 + 1):
            d.set(x, yy, z, block)


# ============================================================================================ furniture
def kitchen(d, seq, y, facing, wood=None, top=None, shelf=True):
    """A run of kitchen units against a wall: seq = [(x, z, kind)], kind in furnace / smoker / crafting_table /
    barrel / sink / counter / fridge / cauldron. `facing` = the side the fronts face (into the room).
    Wall shelves with pots above the counters."""
    wood = wood or d.P["wood"]
    for i, (x, z, k) in enumerate(seq):
        if k in ("furnace", "smoker", "crafting_table", "barrel", "blast_furnace"):
            d.item(x, y, z, k, facing if k != "crafting_table" else None)
        elif k == "sink":
            d.set(x, y, z, "water_cauldron[level=3]")
        elif k == "cauldron":
            d.item(x, y, z, "water_cauldron[level=3]")
        elif k == "fridge":
            d.set(x, y, z, "iron_block")
            d.set(x, y + 1, z, "iron_trapdoor[facing=%s,half=top,open=true,powered=false,waterlogged=false]"
                  % OPP[facing] if False else "iron_block")
        else:
            d.set(x, y, z, top or stair(wood, OPP[facing], "top"))
        if shelf and k in ("counter", "sink", "crafting_table", "barrel") and d.air(x, y + 2, z):
            d.set(x, y + 2, z, slab(wood, "top"))
        if k == "counter" and i % 2 == 0 and d.air(x, y + 1, z):
            d.set(x, y + 1, z, "decorated_pot[cracked=false,facing=north,waterlogged=false]" if i % 4 == 0
                  else "potted_azure_bluet")


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


def shelfwall(d, pts, y, wood=None, items=("decorated_pot", "potted_fern", "candle")):
    wood = wood or d.P["wood"]
    for i, (x, z) in enumerate(pts):
        d.set(x, y, z, slab(wood, "top"))


def rugc(d, x1, z1, x2, z2, y, color):
    for x, z in cells(x1, z1, x2, z2):
        if d.air(x, y, z):
            d.set(x, y, z, f"{color}_carpet")


def garden(d, x1, z1, x2, z2, y, wood, gates=(), flowers=("poppy", "oxeye_daisy", "cornflower", "allium",
                                                            "azure_bluet", "dandelion"), border=True, beds=True):
    """Fenced garden: grass with flower borders inside the fence, gates [(x, z, facing)]."""
    for x, z in cells(x1, z1, x2, z2):
        d.set(x, y - 1, z, "grass_block[snowy=false]")
        d.set(x, y, z, AIR)
    gs = {(gx, gz) for gx, gz, _ in gates}
    for x, z in cells(x1, z1, x2, z2):
        edge = x in (x1, x2) or z in (z1, z2)
        if edge and border:
            if (x, z) not in gs:
                d.set(x, y, z, fence(wood))
        elif beds and (x in (x1 + 1, x2 - 1) or z in (z1 + 1, z2 - 1)) and (x + z) % 2 == 0:
            d.set(x, y, z, flowers[(x * 3 + z) % len(flowers)])
    for gx, gz, f in gates:
        d.set(gx, y, gz, gate(wood, f))


def path(d, pts, y, block):
    for x, z in pts:
        d.set(x, y, z, block)
        if not d.air(x, y + 1, z) and "fence" not in d.get(x, y + 1, z):
            pass


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


def chimney(d, x, z, y1, y2, block="bricks", cap=True):
    for y in range(y1, y2 + 1):
        d.set(x, y, z, block)
    if cap:
        d.set(x, y2 + 1, z, "campfire[facing=north,lit=false,signal_fire=false,waterlogged=false]"
              if False else f"{'brick' if block == 'bricks' else block}_wall"
              f"[east=none,north=none,south=none,up=true,waterlogged=false,west=none]"
              if block in ("bricks", "cobblestone", "mossy_cobblestone", "stone_bricks", "andesite")
              else block)


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
    # mantel shelf in the room
    for k in (-1, 1):
        cx, cz = ix + sx * k, iz + sz * k
        if d.air(cx, y + 1, cz):
            pass
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
                    if under and k > 0 and z1 <= z <= z2:
                        pass
    else:
        lo_edge = z2 if down == "south" else z1
        rows = range(z1, z2 + 1)
        span = [(r, abs(lo_edge - r)) for r in rows]
        for r, k in span + [(lo_edge + dz * overhang, -overhang)]:
            for x in range(x1 - overhang, x2 + overhang + 1):
                if d.bp.inside(x, y + k, r):
                    d.set(x, y + k, r, stair(block, up))


def fill_gable_under(d, x1, z1, x2, z2, y, block):
    """Close the triangle between wall top y-1 and a lean-to roof drawn by shed_roof on the side walls."""
    pass


# ---- Cascadia
def log_walls(d, x1, z1, x2, z2, y1, y2, logb="spruce_log", post="stripped_spruce_log", footing=True, plinth=True):
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


def nt_ribbon(d, x1, z1, x2, z2, y1, y2, glass="glass_pane"):
    """Glazing band on a straight wall segment."""
    d.fill(x1, y1, z1, x2, y2, z2, glass)


def nt_roof(d, x1, z1, x2, z2, y, parapet="white_concrete", coping="smooth_quartz_slab", deck="smooth_quartz"):
    d.flat(x1, z1, x2, z2, y, deck, parapet, coping)


def planter(d, x1, z1, x2, z2, y, plants=("azalea", "flowering_azalea", "fern")):
    for i, (x, z) in enumerate(cells(x1, z1, x2, z2)):
        d.set(x, y, z, "moss_block" if i % 3 else "grass_block[snowy=false]")
        p = plants[i % len(plants)]
        if d.air(x, y + 1, z):
            d.set(x, y + 1, z, p if p != "fern" else "fern")


# ============================================================================================ HOUSE
def house_hw(rel, L):
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
    d.set(x1 + 1, y0 + 2, 10, lantern(False)) if False else None
    rugc(d, 5, 10, 6, 12, y0, "red")
    sofa(d, 7, 10, y0, 3, "south", "east", "dark_oak")
    d.set(5, y0, 9, "potted_red_tulip")
    d.hut(5, y0, 8)
    # dining
    d.dining(10, y0, 10, 2, "z", "dark_oak", ("e", "w"))
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
    partition(d, x1 + 1, yu, z2 - 3, x2 - 1, top - 1 + 1 - 1, z2 - 3, "calcite", (), W) if False else None
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
        d.set(13, yu, bz, "crafting_table") if False else None
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
        for z in range(wz1, wz2 + 1):
            for y in range(5, 11):
                pass
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
        d.set(18, 3, 12, "wall_torch[facing=west]") if False else None
    # ---- L3 porch + garden
    gz2 = z1 - 1
    if L >= 3:
        gz2 = z1 - 2 - (1 if jet else 0)
        garden(d, 2, 1, 21, gz2, y0, "spruce", gates=((9, 1, "north"), (9, gz2, "north")))
        path(d, [(9, z) for z in range(0, z1)], y0 - 1, "gravel")
        clear_above_path(d, [(9, z) for z in range(0, z1)], y0 - 1)
        for z in range(1, z1):
            if d.get(9, y0, z) not in (AIR,) and "gate" not in d.get(9, y0, z):
                d.set(9, y0, z, AIR)
        # garden bench (seats)
        d.chair(5, y0, 3, "west", "spruce")
        d.chair(5, y0, 4, "west", "spruce")
        d.set(6, y0, 3, "flowering_azalea") if False else None
        if L >= 4:
            d.chair(13, y0, 3, "east", "spruce")
            d.chair(13, y0, 4, "east", "spruce")
            d.table(12, y0, 3, "spruce")
        d.set(17, y0, 3, "oak_sapling") if False else None
        d.set(17, y0, 3, "flowering_azalea")
        # porch hood over the door on brackets
        for x in (8, 9, 10):
            d.set(x, y0 + 3, z1 - 1, slab("deepslate_tile"))
        d.set(8, y0 + 2, z1 - 1, stair(W, "south", "top"))
        d.set(10, y0 + 2, z1 - 1, stair(W, "south", "top"))
    else:
        path(d, [(9, z) for z in range(0, z1)], y0 - 1, "gravel")
    d.set(8, y0 + 2, z1 - (2 if jet else 1), "wall_torch[facing=north]") if False else None
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
    d.set(15, y0, z1 - 1, "hay_block[axis=y]") if False else None
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
    d.set(x1 + 1, y0 + 2, 11, "wall_torch[facing=east]") if False else None
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
    d.set(15, y0, 13, "chest[facing=west,type=single,waterlogged=false]") if False else None
    # ---- loft (L3+): deck over the east half, stair along x=10 rising north
    if L >= 3:
        d.fill(11, 6, z1 + 1, x2 - 1, 6, z2 - 1, "spruce_planks")
        d.fill(10, 6, 9, 10, 6, 10, "spruce_planks")
        flight(d, 10, 15, y0, 5, "north", W, support=None)
        for z in range(11, 16):
            pass
        bedset(d, 16, 7, 11, "east", ("r",), "green", W, light="lantern")
        if L >= 5:
            d.bed(16, 7, 13, "east", "lime")
        d.set(15, 7, 14, "chest[facing=north,type=single,waterlogged=false]")
        rugc(d, 12, 11, 14, 13, 7, "green")
        for z in (9, 10):
            d.set(9, 7, z, fence(W)) if False else None
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
        d.set(21, y0 + 1, wz2 - 3, "iron_axe") if False else None
        d.lamp(19, 4, 12)
        d.set(21, y0, 11, "chopping") if False else None
        for z in (11, 12):
            for y in (y0, y0 + 1):
                d.set(21, y, z, log("spruce_log", "x"))
    # ---- L4 back bedroom lean-to
    if L >= 4:
        bx1, bx2, bz1, bz2 = 5, 10, z2, 21
        log_walls(d, bx1, bz1, bx2, bz2, y0, 4, "stripped_spruce_log", LOG)
        d.clear(bx1 + 1, y0, bz1 + 1, bx2 - 1, 4, bz2 - 1)
        log_walls(d, x1, z1, x2, z2, y0, 4, LOG, "stripped_spruce_log", footing=False) if False else None
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


def house_nt(rel, L):
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
    rugc(d, 4, 9, 5, 13, y0, "light_gray")
    sofa(d, 6, 10, y0, 3, "south", "east", "birch", arms=False)
    d.set(6, y0, 9, "birch_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]")
    d.set(4, y0, 7, "potted_bamboo")
    d.hut(5, y0, 7)
    d.dining(9, y0, 10, 2, "x", "birch", ("n", "s"))
    d.set(9, 5, 10, "sea_lantern") if False else None
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
            d.set(x, 9, 9, "sea_lantern") if False else None
            d.set(x, 10, 9, "sea_lantern")
            d.set(x, 10, 14, "sea_lantern")
        d.set(6, 7, 14, "potted_bamboo")
        # glass balustrade at the stair hole
        for x in range(11, 14):
            d.set(x, 7, 13, "glass_pane") if False else None
    # ---- L2 garage workshop (east), under the cantilever from L3
    if L >= 2:
        gx1, gx2, gz1, gz2 = x2, 20, 8, 15
        nt_box(d, gx1, gz1, gx2, gz2, y0, 5, "light_gray_concrete", "light_gray_concrete")
        d.fill(gx1 + 1, 1, gz1 + 1, gx2 - 1, 1, gz2 - 1, "polished_andesite")
        d.clear(gx1 + 1, y0, gz1 + 1, gx2 - 1, 5, gz2 - 1)
        if d.air(gx1 + 1, 6, gz1):
            pass
        for x, z in cells(gx1, gz1, gx2, gz2):
            if d.air(x, 6, z):
                d.set(x, 6, z, "smooth_quartz")
        for x in range(gx1 + 1, gx2):
            d.window(x, y0, gz1, x, 4, gz1, "light_gray_stained_glass_pane")
        d.door(18, y0, gz1, "south", "iron") if False else None
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
        d.item(12, y0, 13, "ender_chest", "west") if False else None
        d.item(13, y0, 7, "ender_chest", "south") if False else None
        d.item(4, y0, 13, "ender_chest", "east")
    # front terrace with planters
    planter(d, x1, z1 - 3, x1 + 2, z1 - 3, 1, ("azalea", "fern", "flowering_azalea"))
    planter(d, 13, z1 - 3, x2, z1 - 3, 1, ("azalea", "fern", "flowering_azalea"))
    return d


@design("house")
def house(pack, rel, L):
    return {"Hearthwood": house_hw, "Cascadia": house_ca, "Neoterra": house_nt}[pack](rel, L)


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
    if d.air(c, y, z + oz):
        d.set(c, y - 1 if not d.air(c, y - 1, z + oz) else y, z + oz,
              trap("spruce", out, "top")) if False else None


def cottage_hw(rel, L):
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
            d.set(x, ridge + 1, z, slab(R)) if False else None
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
    d.lamp(9, 4, z1 + 1) if False else d.set(9, 4, z1 + 1, "lantern[hanging=true,waterlogged=false]")
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
    d.chair(12, y0, 10, "west", "dark_oak", arms=False)
    d.chair(12, y0, 12, "west", "dark_oak", arms=False)
    rugc(d, 13, 10, 13, 12, y0, "green")
    d.set(13, 3, 10, AIR)
    if L >= 3:
        d.bookshelf(11, y0, 13)
        d.item(13, y0, 13, "lectern", "north")
    else:
        d.set(11, y0, 13, "potted_fern")
    if L >= 5:
        d.item(11, y0, 9, "jukebox")
    d.lamp(12, 4, 11)
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
    rugc(d, 6, 9, 7, 12, 6, "light_gray") if False else None
    # ---- garden: picket fence, flower borders, path, a bench and an apple tree corner
    garden(d, 1, 0, 8, z1 - 3, y0, "spruce", ((8, 2, "east"),))
    garden(d, 10, 0, 19, z1 - 3, y0, "spruce", ((10, 2, "west"),))
    for z in range(0, z1):
        d.set(9, 1, z, "gravel")
    clear_above_path(d, [(9, z) for z in range(0, z1)], 1)
    d.set(3, y0, 2, "flowering_azalea")
    d.set(16, y0, 2, "rose_bush[half=lower]")
    d.set(16, y0 + 1, 2, "rose_bush[half=upper]")
    d.chair(4, y0, 1, "north", "spruce", sit=False) if False else None
    d.set(4, y0, 2, "lantern[hanging=false,waterlogged=false]") if False else None
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
        hw_window(d, x1, 3, 11, 1) if False else None
        d.set(x1, y0, 11, AIR)
        d.set(x1, y0 + 1, 11, AIR)
        d.door(x1, y0, 11, "west", "spruce") if False else None
        d.set(2, y0, 10, "water_cauldron[level=3]")
        d.set(2, y0, 12, "barrel[facing=up,open=false]")
        d.set(3, y0, 12, "barrel[facing=east,open=false]")
        hw_window(d, sx1, 3, 11, 1)
        d.set(2, 4, 11, "lantern[hanging=true,waterlogged=false]")
        hw_window(d, x1, 6, 11, 2) if False else None
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


def cottage_ca(rel, L):
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
    d.set(8, y0, 5, "barrel[facing=up,open=false]") if False else None
    d.table(9, y0, 6, W) if False else None
    for x in (x1 - 1, x2 + 1):
        d.set(x, y0 + 1, 3, lantern(False))
    # ---- ground: kitchen under the west slope, hearth on the back wall, bed under the east slope
    d.hut(6, y0, z1 + 1)
    kitchen(d, [(5, 13, "furnace"), (5, 14, "sink"), (5, 15, "smoker"), (5, 16, "crafting_table"),
                (5, 17, "barrel")], y0, "east", W, shelf=False)
    if 2 <= L <= 4:
        d.item(5, y0, 18, "barrel", "east")
    d.table(7, y0, 15, W)
    d.chair(7, y0, 14, "north", W, sit=False)
    d.chair(7, y0, 16, "south", W, sit=False)
    fireplace(d, mid, z2, y0, "north", ridge + 2, "cobblestone", "mossy_cobblestone")
    for y in range(y0 + 2, ridge + 2):
        d.set(mid, y, z2 + 1, "cobblestone" if y % 4 else "mossy_cobblestone")
    rugc(d, 10, 17, 12, 18, y0, "red")
    sofa(d, 10, 16, y0, 3, "east", "north", W)
    bedset(d, 17, y0, 18, "south", (), "red", W)
    nightstand(d, 16, y0, 18, W, "lantern")
    d.set(17, y0, 16, "chest[facing=north,type=single,waterlogged=false]")
    if L >= 3:
        d.bookshelf(17, y0, 10)
        d.item(16, y0, 10, "lectern", "west") if False else d.item(17, y0, 11, "lectern", "west")
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
        d.set(20, 1, 11, "cobblestone") if False else None
        d.set(20, y0, 6, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]") if False else None
        for x, z in cells(19, 9, 22, 13):
            d.set(x, 1, z, "coarse_dirt")
        d.set(21, 1, 11, "cobblestone")
        d.set(21, y0, 11, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        for z in (10, 11, 12):
            d.set(19, y0, z, log("stripped_spruce_log", "z")) if False else None
        d.set(21, y0, 9, log("spruce_log", "x"))
        d.set(22, y0, 9, log("spruce_log", "x"))
        d.set(21, y0, 13, log("spruce_log", "x"))
        d.set(22, y0, 13, log("spruce_log", "x"))
    return d


def cottage_nt(rel, L):
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
    rugc(d, 5, 7, 6, 9, y0, "light_gray")
    sofa(d, 7, 7, y0, 3, "south", "east", W, arms=False)
    d.hut(5, y0, 6)
    kitchen(d, [(5, 11, "barrel"), (6, 11, "furnace"), (7, 11, "sink"), (8, 11, "smoker"),
                (9, 11, "crafting_table")], y0, "north", W, top="smooth_quartz")
    if 2 <= L <= 4:
        d.item(5, y0, 10, "barrel", "east")
    d.set(9, 4, 8, "sea_lantern") if False else None
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


@design("cottage")
def cottage(pack, rel, L):
    return {"Hearthwood": cottage_hw, "Cascadia": cottage_ca, "Neoterra": cottage_nt}[pack](rel, L)


# ============================================================================================ studio flat template
CCW = {v: k for k, v in CW.items()}


def flat(d, ox, oz, y, out, mirror=False, wood=None, top=None, bedc=None, ceil=None, lamp="lantern",
         sofa_seats=True, extra=None, extra_barrel=False, double=False):
    """Furnish a 7 x 6 studio flat. Local (0,0) is the interior corner on the window wall (`out` = world direction
    of that wall); local x runs along the window wall (to CW[out], or CCW when mirrored), local z runs inward.
    Free cells for the entrance: local row z=5 (x3..6) and the local-east side at z=5.
      z0: bed  stand chest .  .  .  furnace
      z1: bed  .    .    ch .  .  sink
      z2: .    .    ch   T  ch .  smoker
      z3: sofa rug  .    ch .  .  crafting
      z4: sofa rug  .    .  .  .  barrel
      z5: plant .   .    .  .  .  .
    Returns {'door': [...free entrance cells...]}."""
    wood = wood or d.P["wood"]
    E = CCW[out] if mirror else CW[out]
    S = OPP[out]
    ex, ez = D4[E]
    sx, sz = D4[S]

    def W(lx, lz):
        return ox + ex * lx + sx * lz, oz + ez * lx + sz * lz

    def dirl(c):
        return {"N": out, "S": S, "E": E, "W": OPP[E]}[c]
    x, z = W(0, 0)
    d.bed(x, y, z, out, bedc)
    if double:
        x, z = W(1, 0)
        d.bed(x, y, z, out, bedc)
        x, z = W(2, 0)
        nightstand(d, x, y, z, wood, "candle")
    else:
        x, z = W(1, 0)
        nightstand(d, x, y, z, wood, "candle")
        x, z = W(2, 0)
        d.set(x, y, z, f"chest[facing={S},type=single,waterlogged=false]")
    if extra_barrel:
        x, z = W(5, 0)
        d.item(x, y, z, "barrel", S)
    for lz, k in enumerate(("furnace", "sink", "smoker", "crafting_table", "barrel")):
        x, z = W(6, lz)
        if k == "sink":
            d.set(x, y, z, "water_cauldron[level=3]")
        else:
            d.item(x, y, z, k, dirl("W") if k != "crafting_table" else None)
        if k in ("sink", "crafting_table", "barrel") and ceil and ceil - y >= 3:
            d.set(x, y + 2, z, slab(top or wood, "top") if top and "slab" in (top or "") else slab(wood, "top"))
    x, z = W(3, 2)
    if top:
        d.set(x, y, z, top)
    else:
        d.table(x, y, z, wood)
    for (lx, lz), back in (((3, 1), "N"), ((3, 3), "S"), ((2, 2), "W"), ((4, 2), "E")):
        x, z = W(lx, lz)
        d.chair(x, y, z, dirl(back), wood)
    for lz in (3, 4):
        x, z = W(0, lz)
        d.chair(x, y, z, dirl("W"), wood, sit=sofa_seats)
        x, z = W(1, lz)
        d.set(x, y, z, f"{(bedc or d.P['bed'])}_carpet")
    x, z = W(0, 5)
    d.set(x, y, z, d.P["plant"])
    if ceil:
        x, z = W(3, 3)
        if lamp == "lantern":
            d.set(x, ceil, z, lantern(True))
        else:
            d.set(x, ceil + 1, z, lamp)
    return W


# ============================================================================================ APARTMENT
def apartment_nt(rel, L):
    d = Design("Neoterra", rel, (17, 34, 21), paving="smooth_stone")
    x1, x2, z1, z2 = 3, 11, 5, 16
    H = 5
    F = L
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
        W = flat(d, x1 + 1, z1 + 1, Y, "north", wood="birch", top="smooth_quartz", bedc="cyan", ceil=Y + 3)
        partition(d, x1 + 1, 12, x2 - 1, 12, Y, Y + 3, "white_concrete", ((9, 12, "north"),), "birch")
        # street glazing, side strip windows
        for x in range(x1 + 1, x2):
            d.window(x, Y, z1, x, Y + 3, z1)
        d.set(x1, Y + 3, z1, "light_gray_concrete")
        for z in (8, 10):
            d.window(x1, Y + 1, z, x1, Y + 2, z)
            d.window(x2, Y + 1, z, x2, Y + 2, z)
        d.window(x2, Y + 1, 14, x2, Y + 2, 15, "light_gray_stained_glass_pane")
        d.window(5, Y + 1, z2, 9, Y + 2, z2, "light_gray_stained_glass_pane")
        d.set(7, Y + 3, 13, "sea_lantern") if False else None
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
            d.set(9, Y, z1 - 1, "potted_bamboo") if False else None
            d.set(5, Y, z1 - 1, "potted_bamboo")
            if f % 2:
                d.set(9, Y, z1 - 1, "azalea")
    # stair core: alternate rows z=15 (rise east) / z=14 (rise west)
    for f in range(F - 1 + (1 if L >= 4 else 0)):
        Y = 2 + H * f
        if f % 2 == 0:
            flight(d, 5, 15, Y, H, "east", "smooth_quartz")
        else:
            flight(d, 9, 14, Y, H, "west", "smooth_quartz")
        d.set(7, Y + 3, 13, "sea_lantern")
    # roof
    if L >= 4:
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
        d.set(7, yt + 2, 13, "glass_pane") if False else None
        # terrace: planters, loungers, pergola lights
        planter(d, x1 + 1, z1 + 1, x2 - 1, z1 + 1, yt - 1 + 0, ("azalea", "fern", "flowering_azalea")) \
            if False else None
        for x in range(x1 + 1, x2):
            d.set(x, yt, z1 + 1, "moss_block" if x % 2 else "flowering_azalea")
        d.chair(5, yt, 9, "west", "birch", sit=False)
        d.chair(5, yt, 10, "west", "birch", sit=False)
        d.table(6, yt, 9, "birch", "slab", "smooth_quartz_slab")
        d.chair(9, yt, 9, "east", "birch", sit=False)
        d.chair(9, yt, 10, "east", "birch", sit=False)
        d.set(7, yt, 11, "lantern[hanging=false,waterlogged=false]")
        for x in (x1 + 1, x2 - 1):
            for y in range(yt, yt + 3):
                d.set(x, y, z1 + 2, "end_rod[facing=up]" if y == yt + 2 else "white_concrete_wall") \
                    if False else None
        # solar panels on the stair hut
        for x in range(4, 11):
            d.set(x, yt + 4, 14, "daylight_detector[inverted=false,power=0]")
    else:
        d.flat(x1, z1, x2, z2, yt - 1, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
        for x in range(4, 11):
            d.set(x, yt + 1, 14, "daylight_detector[inverted=false,power=0]") if False else None
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


def apartment_hw(rel, L):
    d = Design("Hearthwood", rel, (27, 26, 19), paving="grass_block[snowy=false]")
    x1, x2, z1, z2 = 3, 23, 5, 12
    H = 4
    F = {1: 1, 2: 2, 3: 2, 4: 3, 5: 3}[L]
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
        flat(d, 4, 6, Y, "north", False, "dark_oak", None, "red", Y + 2)
        flat(d, 22, 6, Y, "north", True, "dark_oak", None, "blue", Y + 2)
        for x in (6, 8, 10, 16, 18, 20):                             # sash windows
            d.window(x, Y + 1, z1, x, Y + 2, z1)
        for x in (6, 8, 18, 20):
            d.window(x, Y + 1, z2, x, Y + 2, z2)
        for x in (13,):
            if f:
                d.window(x, Y + 1, z1, x, Y + 2, z1)
        d.set(13, Y + 2, 9, lantern(True))
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
        d.set(xw, ridge + 3, 8, "flower_pot") if False else None
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
    if L >= 2:
        garden(d, x1, z2 + 2, x2, 18, 2, "dark_oak", ((13, z2 + 2, "north"),))
        for z in range(z2 + 1, 18):
            d.set(13, 1, z, "gravel")
        clear_above_path(d, [(13, z) for z in range(z2 + 1, 18)], 1)
        for x in (6, 20):
            d.set(x, 2, 16, "flowering_azalea")
        d.chair(9, 2, 17, "south", "dark_oak", sit=False)
        d.chair(10, 2, 17, "south", "dark_oak", sit=False)
    return d


def apartment_ca(rel, L):
    d = Design("Cascadia", rel, (31, 22, 19), paving="grass_block[snowy=false]")
    B = {1: 2, 2: 2, 3: 3, 4: 3, 5: 3}[L]
    F = 1 if L == 1 else 2
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
            flat(d, ox, z2 - 1, Y, "south", True, "spruce", None, ("brown", "green", "orange")[k], Y + 3)
            d.door(ox + 4, Y, z1, "south", "spruce")
            ca_window(d, ox + 1, Y + 1, z1, "north", 2, w=2)
            for x in (ox + 3, ox + 5):
                ca_window(d, x, Y + 1, z2, "south", 2, shutters=False)
            d.set(ox + 4, Y + 2, z1 - 1, lantern(False)) if False else None
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
        for z in range(7, 12):
            d.set(0, 7 if z < 7 else 2 + (11 - z), z, fence("spruce")) if False else None
        d.set(1, 7, 3, fence("spruce"))
        d.set(2, 7, 3, fence("spruce"))
        for z in (4, 5):
            d.set(0, 7, z, fence("spruce")) if False else None
    else:
        for x in range(x1 - 1, x2 + 2):
            for z in (2, 3, 4, 5):
                d.set(x, top, z, stair("dark_oak", "south"))
    for k in range(B):
        d.set(x1 + 2 + 8 * k, top - 1 if F == 1 else 5, 4, lantern(True))
        if F == 2:
            d.set(x1 + 2 + 8 * k, 10, 4, lantern(True)) if top > 10 else None
    for x in range(x1 + 1, x2):
        if (x - x1) % 8 in (2, 3) and x < x2 - 1:
            pass
    d.chair(x1 + 1, 2, 4, "north", "spruce", sit=False)
    d.chair(x1 + 2, 2, 4, "north", "spruce", sit=False)
    d.keg(x1 + 3, 2, 4, "east") if False else None
    d.sign(x1 + 8 * B // 2, top - 1 if F == 1 else 5, 2, "north", ["", "PINE HOLLOW", "ROOMS"], "spruce") \
        if False else None
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


@design("apartment")
def apartment(pack, rel, L):
    return {"Neoterra": apartment_nt, "Hearthwood": apartment_hw, "Cascadia": apartment_ca}[pack](rel, L)


# ============================================================================================ QUADPLEX
def quadplex_hw(rel, L):
    d = Design("Hearthwood", rel, (31, 22, 21), paving="grass_block[snowy=false]")
    U = min(L, 4)
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
        d.chair(a + 2, 2, 8, "east", W)
        d.chair(a + 2, 2, 10, "east", W)
        d.set(a + 1, 2, 9, "red_carpet")
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
        garden(d, a - 1, 1, a + 5, z1 - 2, 2, "spruce", ((a + 1, 1, "north"),))
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


def cabin(d, x1, z1, out, mirror, Y, bedc, extra_barrel=True, double=False, porch=True):
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
    Wf = flat(d, ox, oz, Y, out, mirror, "spruce", None, bedc, Y + 3, extra_barrel=extra_barrel, double=double)
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
                d.set(x, Y + 3, z, stair("spruce", OPP[OPP[out]] if False else out))
        for x in range(x1 + 1, x2):
            if abs(x - dx) > 1:
                d.set(x, Y, pz, fence("spruce"))
        d.set(dx + 2 if dx + 2 < x2 else dx - 2, Y, porch_z[0] if out == "north" else porch_z[1],
              stair("spruce", out))
        d.set(dx, Y + 2, pz, lantern(True)) if False else None
    return Wf


def quadplex_ca(rel, L):
    d = Design("Cascadia", rel, (27, 20, 29), paving="grass_block[snowy=false]")
    U = min(L, 4)
    spec = [(1, 2, "north", False, "brown"), (17, 2, "north", True, "green"),
            (1, 19, "south", True, "orange"), (17, 19, "south", False, "cyan")]
    for k in range(U):
        x1, z1, out, mir, c = spec[k]
        Wf = cabin(d, x1, z1, out, mir, 2, c, True, double=(k == 0 and L >= 5))
        if k == 0:
            hx, hz = Wf(4, 0)
            d.hut(hx, 2, hz)
    # courtyard: gravel paths, fire ring with log benches
    for x, z in cells(3, 12, 23, 16):
        d.set(x, 1, z, "coarse_dirt" if (x * 3 + z) % 4 else "gravel")
    for z in range(0, 29):
        d.set(13, 1, z, "gravel")
    d.set(13, 1, 14, "cobblestone")
    d.set(13, 2, 14, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for x, z, b in ((11, 14, "west"), (15, 14, "east")):
        d.chair(x, 2, z - 1, b, "spruce", sit=False) if False else None
    for x in (12, 13, 14):
        d.set(x, 2, 12, log("spruce_log", "x"))
        d.set(x, 2, 16, log("spruce_log", "x"))
    for (x, z) in ((3, 13), (23, 13)):
        d.set(x, 2, z, lantern(False)) if False else None
    if L >= 5:
        # common pavilion: open timber shelter with a jukebox and the ender chest
        for x, z in cells(9, 0, 17, 0):
            pass
        px1, px2, pz1, pz2 = 19, 25, 11, 17
        for x, z in cells(px1, pz1, px2, pz2):
            d.set(x, 1, z, "spruce_planks")
        for x, z in ((px1, pz1), (px2, pz1), (px1, pz2), (px2, pz2)):
            for y in range(2, 5):
                d.set(x, y, z, log("spruce_log", "y"))
        d.gable(px1, pz1, px2, pz2, 5, "z", "dark_oak_stairs", "dark_oak_slab", "spruce_planks")
        d.item(px2 - 1, 2, 14, "jukebox")
        d.item(px2 - 1, 2, 13, "ender_chest", "west")
        d.dining(22, 2, 14, 1, "x", "spruce", ("n", "s", "w"))
        d.set(22, 4, 14, lantern(True))
    return d


def quadplex_nt(rel, L):
    d = Design("Neoterra", rel, (31, 20, 21), paving="smooth_stone")
    U = min(L, 4)
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
        sofa(d, a, z1 + 3, 2, 2, "east", "south", W, arms=False)
        d.set(a, 2, z1 + 1, "potted_bamboo")
        rugc(d, a, z1 + 2, a + 2, z1 + 2, 2, "cyan")
        d.table(a + 1, 2, z1 + 6, W, "slab", "smooth_quartz_slab")
        d.chair(a, 2, z1 + 6, "west", W)
        d.chair(a + 2, 2, z1 + 6, "east", W)
        kitchen(d, [(a, z2 - 1, "furnace"), (a + 1, z2 - 1, "sink"), (a + 2, z2 - 1, "smoker"),
                    (a + 3, z2 - 1, "crafting_table")], 2, "north", W, top="smooth_quartz")
        d.item(a + 4, 2, z2 - 1, "barrel", "north")
        d.item(a + 4, 2, z2 - 2, "barrel", "west")
        d.set(a + 1, 4, z1 + 4, "sea_lantern") if False else None
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


@design("quadplex")
def quadplex(pack, rel, L):
    return {"Hearthwood": quadplex_hw, "Cascadia": quadplex_ca, "Neoterra": quadplex_nt}[pack](rel, L)


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
    d.double_door(12, y0, z1, "x", "south", W) if False else d.door(12, y0, z1, "south", W)
    d.set(12, y0 + 2, z1, "stone_bricks")
    for y in (y0, y0 + 1):
        d.set(11, y, z1 - 2, "stone_brick_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
        d.set(13, y, z1 - 2, "stone_brick_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
    d.set(11, y0 + 2, z1 - 2, stair("stone_brick", "west", "top"))
    d.set(13, y0 + 2, z1 - 2, stair("stone_brick", "east", "top"))
    d.set(12, y0 + 2, z1 - 2, "stone_bricks") if False else None
    d.set(12, y0 + 3, z1 - 2, "stone_bricks")
    d.set(12, y0 + 2, z1 - 1, lantern(True))
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
    d.dining(6, y0, 10, 3, "x", W, ("n",)) if False else None
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
        d.bookshelf(18, yu, 4) if False else d.set(18, yu, 4, "bookshelf")
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
        d.door(11, y0, bz1, "south", "spruce") if False else d.set(11, y0, bz1, "stone_bricks")
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
        for x, z in cells(22, 23, 27, 19):
            pass
        d.item(23, y0, 20, "anvil", "east")
        if L >= 3:
            d.item(25, y0, 20, "anvil", "east")
        d.set(27, y0, 17, "water_cauldron[level=3]")
        d.item(27, y0, 16, "barrel", "west") if False else None
        d.set(24, 5, 20, lantern(True))
        # kitchen garden with composter and a bench
        garden(d, 20, 26, 29, 28, y0, "spruce", ((20, 27, "west"),), beds=False)
        for x in range(21, 29):
            d.set(x, 1, 27, "farmland[moisture=7]")
            d.set(x, y0, 27, ("carrots[age=7]", "potatoes[age=7]", "wheat[age=7]")[x % 3])
        d.item(28, y0, 26, "composter") if False else None
        d.item(19, y0, 26, "composter")
        d.set(19, 1, 26, "grass_block[snowy=false]")
    # front lawn with a bench, and a back terrace with garden table (L5)
    for x in range(1, 30):
        if abs(x - 12) > 1:
            d.set(x, y0, 0, "spruce_fence" if False else fence("spruce"))
    for z in range(0, z1 - 2):
        d.set(12, 1, z, "gravel")
    if L >= 5:
        for x, z in cells(20, 4, 28, 11):
            d.set(x, 1, z, "stone_bricks" if (x + z) % 2 else "polished_andesite")
        d.dining(23, y0, 7, 2, "x", "spruce", ("n", "s"))
        d.set(21, y0, 4, "flowering_azalea")
        d.set(27, y0, 10, "flowering_azalea")
        d.set(21, y0 + 1, 10, lantern(False)) if False else None
    return d


@design("playerhouse")
def playerhouse(pack, rel, L):
    return {"Hearthwood": playerhouse_hw}[pack](rel, L)
