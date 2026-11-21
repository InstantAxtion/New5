"""
Civic & education landmarks: townhall, hospital, library, school, university, communitycollege.

Every type grows from a modest working core (L1) into a complex (L5): new wings, storeys, towers and additional
buildings with furnished rooms. Shared building blocks: bldg() shells with storey bands, quoins, sills/shutters,
eave brackets, roofs and lights; room furnishers (office, dorm, ward, classroom, lab, lecture, kitchen, ...);
outdoor pieces (lawns, bordered paths, flower beds, trees, lamps, benches, fountains, market stalls).
Each type has its own palette inside each pack (THEMES).
"""
from hm import Design, design, AIR, D4, OPP, CW

Y0 = 2   # first walkable layer


# ============================================================================================ helpers
def st(block, facing, half="bottom", shape="straight"):
    return f"{block}[facing={facing},half={half},shape={shape},waterlogged=false]"


def slab(block, typ="bottom"):
    return f"{block}[type={typ},waterlogged=false]"


def log(block, axis="y"):
    return f"{block}[axis={axis}]"


def flight(d, x, z, y0, yU, rise, block, under=None, width=1, side="east"):
    """Straight stair flight: first step at (x, y0, z), rising toward `rise` until the top step sits in the floor
    layer yU-1 (you step off onto the floor at yU). Headroom (3 blocks, for the jump) is cleared above every step.
    `width` extends the flight toward `side`. Returns the landing cell (x, z) on the upper floor."""
    dx, dz = D4[rise]
    sx, sz = D4[side]
    n = yU - y0
    for w in range(width):
        for i in range(n):
            cx, cz = x + dx * i + sx * w, z + dz * i + sz * w
            y = y0 + i
            d.set(cx, y, cz, st(block, rise))
            if under:
                for yy in range(y0, y):
                    d.set(cx, yy, cz, under)
            for yy in range(y + 1, y + 4):
                if d.bp.inside(cx, yy, cz):
                    d.set(cx, yy, cz, AIR)
    return x + dx * n, z + dz * n


def shelves(d, x1, z1, x2, z2, y, h=1):
    """Run of bookshelves (h high) on every free cell of the line/rectangle."""
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for z in range(min(z1, z2), max(z1, z2) + 1):
            for k in range(h):
                if d.air(x, y + k, z) and (x, y + k, z) not in getattr(d, "res", ()):
                    d.bookshelf(x, y + k, z)


def rail(d, x1, z1, x2, z2, y, fence):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for z in range(min(z1, z2), max(z1, z2) + 1):
            if d.air(x, y, z):
                d.set(x, y, z, fence)


def beams(d, x1, x2, z1, z2, y, blk, every=4, axis="z"):
    """Exposed tie beams across a room (axis = direction the beam runs)."""
    if axis == "z":
        for x in range(x1, x2 + 1, every):
            for z in range(z1, z2 + 1):
                d.set(x, y, z, log(blk, "z"))
    else:
        for z in range(z1, z2 + 1, every):
            for x in range(x1, x2 + 1):
                d.set(x, y, z, log(blk, "x"))


def framing(d, x1, z1, x2, z2, y1, y2, post, every=2, sill=True):
    """Tudor framing on a calcite wall rectangle: posts every `every`, sill and head beams."""
    for x in range(x1, x2 + 1):
        for z in (z1, z2):
            if (x - x1) % every == 0 or x == x2:
                for y in range(y1, y2 + 1):
                    if not d.get(x, y, z).endswith("pane") and "door" not in d.get(x, y, z):
                        d.set(x, y, z, log(post, "y"))
            d.set(x, y2, z, log(post, "x"))
            if sill:
                d.set(x, y1, z, log(post, "x"))
    for z in range(z1, z2 + 1):
        for x in (x1, x2):
            if (z - z1) % every == 0 or z == z2:
                for y in range(y1, y2 + 1):
                    if not d.get(x, y, z).endswith("pane") and "door" not in d.get(x, y, z):
                        d.set(x, y, z, log(post, "y"))
            d.set(x, y2, z, log(post, "z"))
            if sill:
                d.set(x, y1, z, log(post, "z"))


def clockface(d, x, y, z, facing, face="quartz_block", frame=None, hand="black_concrete"):
    """3x3 clock face centred at (x,y,z) in a wall facing `facing` (hands at three o'clock)."""
    ax = (1, 0) if facing in ("north", "south") else (0, 1)
    for a in (-1, 0, 1):
        for b in (-1, 0, 1):
            d.set(x + ax[0] * a, y + b, z + ax[1] * a, face)
    right = {"north": -1, "south": 1, "east": -1, "west": 1}[facing]   # viewer's right
    d.set(x, y, z, hand)
    d.set(x, y + 1, z, hand)
    d.set(x + ax[0] * right, y, z + ax[1] * right, hand)
    if frame:
        fx, fz = D4[facing]
        for a in (-1, 1):
            d.set(x + ax[0] * a * 2, y, z + ax[1] * a * 2, frame)


def desk_rows(d, x1, x2, z1, z2, y, board, wood, top, every_x=3, need=None):
    """Classroom: rows of desk + chair pairs facing the board side (`board` = north/south/east/west).
    Desks are in pairs across, aisles between. Returns the number of seats placed."""
    n = 0
    bx, bz = D4[board]
    back = OPP[board]
    if board in ("north", "south"):
        rows = range(z1, z2, 2) if board == "north" else range(z2, z1, -2)
        for r in rows:
            for x in range(x1, x2 + 1):
                if every_x and (x - x1) % every_x == every_x - 1:
                    continue
                if need is not None and n >= need:
                    return n
                d.table(x, y, r, wood, "slab", top)
                d.chair(x, y, r - bz, back, wood)
                n += 1
    else:
        cols = range(x1, x2, 2) if board == "west" else range(x2, x1, -2)
        for c in cols:
            for z in range(z1, z2 + 1):
                if every_x and (z - z1) % every_x == every_x - 1:
                    continue
                if need is not None and n >= need:
                    return n
                d.table(c, y, z, wood, "slab", top)
                d.chair(c - bx, y, z, back, wood)
                n += 1
    return n


def blackboard(d, x1, z1, x2, z2, y, facing, blk="black_concrete", frame="dark_oak"):
    """Chalkboard hung on a wall face (cells just inside the wall), 2 high from y, chalk ledge below."""
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for z in range(min(z1, z2), max(z1, z2) + 1):
            d.set(x, y, z, blk)
            d.set(x, y + 1, z, blk)
            d.set(x, y - 1, z, f"{frame}_trapdoor[facing={facing},half=top,open=false,powered=false,waterlogged=false]")


def ward_row(d, x1, x2, z, y, head, color, n, curtain="white_stained_glass_pane", step=2):
    """Row of hospital beds along x from x1, heads at row z pointing `head` (north/south), curtains between.
    Returns beds placed."""
    k = 0
    fz = D4[OPP[head]][1]
    for x in range(x1, x2 + 1, step):
        if k >= n:
            break
        d.bed(x, y, z, head, color)
        k += 1
        if x + 1 <= x2 and k < n:
            for zz in (z, z + fz):
                d.set(x + 1, y, zz, curtain)
                d.set(x + 1, y + 1, zz, curtain)
    return k


def ward_col(d, x, z1, z2, y, head, color, n, curtain="white_stained_glass_pane", step=2):
    k = 0
    fx = D4[OPP[head]][0]
    for z in range(z1, z2 + 1, step):
        if k >= n:
            break
        d.bed(x, y, z, head, color)
        k += 1
        if z + 1 <= z2 and k < n:
            for xx in (x, x + fx):
                d.set(xx, y, z + 1, curtain)
                d.set(xx, y + 1, z + 1, curtain)
    return k


def bench(d, x1, z1, x2, z2, y, back, wood, tag="sit"):
    """Bench / pew of stairs; every cell is a seat tagged `tag` ("sit", "sit_out" or None for decoration)."""
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for z in range(min(z1, z2), max(z1, z2) + 1):
            d.chair(x, y, z, back, wood, sit=(tag == "sit"))
            if tag and tag != "sit":
                d.tag(x, y, z, tag)
                d.placed.setdefault("tagged", {}).setdefault(tag, 0)
                d.placed["tagged"][tag] += 1


def tree(d, x, y, z, logb="oak_log", leaves="oak_leaves", h=4, r=2):
    for k in range(h):
        d.set(x, y + k, z, log(logb))
    for dy in range(h - 2, h + 2):
        rr = r if dy < h else r - 1
        for a in range(-rr, rr + 1):
            for b in range(-rr, rr + 1):
                if abs(a) + abs(b) <= rr + (1 if dy == h - 1 else 0) and d.air(x + a, y + dy, z + b):
                    d.set(x + a, y + dy, z + b, f"{leaves}[distance=1,persistent=true,waterlogged=false]")


def lamppost(d, x, y, z, post, lamp="lantern", h=3):
    for k in range(h):
        d.set(x, y + k, z, post)
    d.set(x, y + h, z, f"{lamp}[hanging=false,waterlogged=false]" if "lantern" in lamp else lamp)


def bell(d, x, y, z, facing="north"):
    d.set(x, y, z, f"bell[attachment=ceiling,facing={facing},powered=false]")


def count(d, key):
    return d.placed["items"].get("minecraft:" + key, 0)


def need(d, key):
    return d.req["items"].get("minecraft:" + key, 0)


def shelf_runs(d, runs, target):
    """Place whole bookshelf runs (x1, z1, x2, z2, y, h) in order until `target` shelves are placed."""
    for r in runs:
        if d.placed["bookshelves"] >= target:
            break
        shelves(d, *r)


def sit_out(d, x, y, z, back, wood):
    d.chair(x, y, z, back, wood, sit=False)
    d.tag(x, y, z, "sit_out")


# ############################################################################################################
#  ROUND 2: modular complexes – every level adds real buildings / storeys, all rooms furnished and decorated
# ############################################################################################################
STY = {
    "Hearthwood": dict(wall="bricks", up="calcite", base="stone_bricks", post="stripped_dark_oak_log",
                       band="dark_oak_planks", floor="oak_planks", wood="dark_oak", wood2="oak",
                       roof="deepslate_tile", glass="glass_pane", shutter="spruce_trapdoor", sill="dark_oak_trapdoor",
                       lamp="lantern", rug=("red_carpet", "orange_carpet"), bed="red", path="gravel",
                       border="stone_brick_wall", flowers=("red_tulip", "oxeye_daisy", "cornflower", "allium")),
    "Cascadia": dict(wall="stripped_spruce_log", up="stripped_spruce_log", base="cobblestone", post="spruce_log",
                     band="spruce_log", floor="spruce_planks", wood="spruce", wood2="dark_oak",
                     roof="dark_oak", glass="glass_pane", shutter="spruce_trapdoor", sill="spruce_trapdoor",
                     lamp="lantern", rug=("brown_carpet", "green_carpet"), bed="brown", path="coarse_dirt",
                     border="cobblestone_wall", flowers=("fern", "blue_orchid", "lily_of_the_valley", "dandelion")),
    "Neoterra": dict(wall="white_concrete", up="white_concrete", base="light_gray_concrete", post="light_gray_concrete",
                     band="cyan_terracotta", floor="polished_diorite", wood="birch", wood2="mangrove",
                     roof="smooth_quartz", glass="glass_pane", shutter=None, sill="smooth_quartz_slab",
                     lamp="sea_lantern", rug=("cyan_carpet", "light_gray_carpet"), bed="cyan", path="smooth_stone",
                     border="smooth_quartz_slab", flowers=("bamboo", "azure_bluet", "white_tulip", "cactus")),
}
OUT = {"n": "north", "s": "south", "e": "east", "w": "west"}


# per-type palettes inside each pack (roof / walls / trim / accent differ between building types)
THEMES = {
    ("Hearthwood", "townhall"): dict(roof="deepslate_tile", wall="stone_bricks", up="calcite", post="stripped_dark_oak_log",
                                     shutter="mangrove_trapdoor", band="dark_oak_planks"),
    ("Hearthwood", "hospital"): dict(roof="dark_oak", wall="bricks", up="calcite", post="stripped_oak_log",
                                     shutter="warped_trapdoor", band="oak_planks", wood="oak", sill="oak_trapdoor"),
    ("Hearthwood", "library"): dict(roof="mud_brick", wall="smooth_sandstone", up="smooth_sandstone",
                                    shutter="dark_oak_trapdoor", base="sandstone"),
    ("Hearthwood", "school"): dict(roof="brick", wall="yellow_terracotta", up="yellow_terracotta",
                                   post="stripped_oak_log", shutter="warped_trapdoor", wood="oak", band="oak_planks"),
    ("Hearthwood", "university"): dict(roof="dark_prismarine", wall="stone_bricks", up="stone_bricks",
                                       shutter="spruce_trapdoor"),
    ("Hearthwood", "communitycollege"): dict(roof="granite", wall="white_terracotta", up="white_terracotta",
                                             shutter="bamboo_trapdoor", post="stripped_dark_oak_log"),
    ("Cascadia", "townhall"): dict(roof="dark_oak", wall="stripped_spruce_log", shutter="mangrove_trapdoor"),
    ("Cascadia", "hospital"): dict(roof="dark_prismarine", wall="birch_planks", up="birch_planks",
                                   post="stripped_birch_log", band="spruce_log", shutter="mangrove_trapdoor"),
    ("Cascadia", "library"): dict(roof="mangrove", wall="stripped_dark_oak_log", up="stripped_dark_oak_log",
                                  post="spruce_log", shutter="warped_trapdoor", base="tuff"),
    ("Cascadia", "school"): dict(roof="spruce", wall="mangrove_planks", up="mangrove_planks", post="stripped_birch_log",
                                 shutter="birch_trapdoor", band="stripped_birch_log"),
    ("Cascadia", "university"): dict(roof="deepslate_tile", wall="stripped_spruce_log", shutter="warped_trapdoor",
                                     base="andesite"),
    ("Cascadia", "communitycollege"): dict(roof="warped", wall="spruce_planks", up="spruce_planks",
                                           post="stripped_spruce_log", shutter="bamboo_trapdoor"),
    ("Neoterra", "townhall"): dict(band="cyan_terracotta", wall="white_concrete"),
    ("Neoterra", "hospital"): dict(band="lime_terracotta", wall="white_concrete", base="light_gray_concrete"),
    ("Neoterra", "library"): dict(band="orange_terracotta", wall="white_terracotta", up="birch_planks",
                                  base="polished_deepslate"),
    ("Neoterra", "school"): dict(band="yellow_concrete", wall="light_gray_concrete", up="light_gray_concrete"),
    ("Neoterra", "university"): dict(band="magenta_terracotta", wall="light_gray_concrete", up="white_concrete",
                                     base="polished_blackstone"),
    ("Neoterra", "communitycollege"): dict(band="orange_concrete", wall="white_concrete", up="mangrove_planks",
                                           base="gray_concrete"),
}


# levels 1-3 build in common materials; premium ones (quartz, prismarine, sea lanterns, end rods, blackstone)
# only appear from level 4 as the building is upgraded
DOWNGRADE = [("smooth_quartz_stairs", "polished_diorite_stairs"), ("smooth_quartz_slab", "smooth_stone_slab"),
             ("smooth_quartz", "smooth_stone"), ("quartz_pillar", "stripped_birch_log"),
             ("quartz_block", "calcite"), ("quartz_stairs", "polished_diorite_stairs"),
             ("quartz_slab", "smooth_stone_slab"), ("sea_lantern", "glowstone"),
             ("polished_blackstone", "polished_andesite")]


def common_materials(d):
    """Swap premium blocks for common ones on levels 1-3 (keeps the block states)."""
    if d.level >= 4:
        return d
    roofwood = {"Hearthwood": "spruce", "Cascadia": "spruce", "Neoterra": "smooth_stone"}[d.pack]
    grid = d.bp.grid
    for y in range(len(grid)):
        for z in range(len(grid[y])):
            row = grid[y][z]
            for x, stt in enumerate(row):
                if stt == AIR:
                    continue
                name = stt.split("[")[0].split(":")[-1]
                props = stt[len(stt.split("[")[0]):]
                new_name = None
                if name.startswith("dark_prismarine"):
                    new_name = name.replace("dark_prismarine", roofwood)
                elif name == "end_rod":
                    new_name, props = "lantern", "[hanging=false,waterlogged=false]"
                else:
                    for a, b in DOWNGRADE:
                        if name == a or (a == "sea_lantern" and name == a):
                            new_name = b
                            break
                if new_name:
                    if new_name == "stripped_birch_log" and "axis" not in props:
                        props = "[axis=y]"
                    if new_name in ("smooth_stone", "calcite", "glowstone", "polished_andesite"):
                        props = ""
                    row[x] = "minecraft:" + new_name + props
    return d


def new(pack, rel, size, **kw):
    d = Design(pack, rel, size, gy=1, **kw)
    d.res = set()
    d.S = dict(STY[pack])
    d.S.update(THEMES.get((pack, d.req["base"]), {}))
    return d


def put(d, x, y, z, b, te=None):
    if not d.bp.inside(x, y, z) or not d.air(x, y, z) or (x, y, z) in d.res:
        return False
    d.set(x, y, z, b, te)
    return True


def keep(d, x, y, z, h=2):
    for k in range(h):
        d.res.add((x, y + k, z))


def wallblock(d, mat, side):
    if mat.endswith("_log") or mat.endswith("_wood"):
        return log(mat, "x" if side in ("n", "s") else "z")
    return mat


def bldg(d, x1, z1, x2, z2, nf=1, roof="gable", axis="x", win="nesw", ws=3, mat=None, up=None, wh=4,
         gable_end=None, beams_on=True, deco=True, glassy=False, parapet=True):
    """A building shell: plinth, walls per storey (wh high + floor slab), corner posts, storey bands, windows with
    sills/shutters, roof (gable/hip/flat) with eave brackets, tie beams and lights. Returns dict(ys, top, ridge)."""
    S = d.S
    mat = mat or S["wall"]
    up = up or S["up"]
    fh = wh + 1
    ys = [Y0 + fh * f for f in range(nf)]
    top = ys[-1] + wh - 1
    d.fill(x1, 1, z1, x2, 1, z2, S["floor"] if d.pack != "Neoterra" else "polished_diorite")
    for f, y in enumerate(ys):
        m = mat if f == 0 else up
        for yy in range(y, y + (wh if f == nf - 1 else fh)):
            for x in range(x1, x2 + 1):
                d.set(x, yy, z1, wallblock(d, m, "n"))
                d.set(x, yy, z2, wallblock(d, m, "s"))
            for z in range(z1 + 1, z2):
                d.set(x1, yy, z, wallblock(d, m, "w"))
                d.set(x2, yy, z, wallblock(d, m, "e"))
            if yy < y + wh:
                d.clear(x1 + 1, yy, z1 + 1, x2 - 1, yy, z2 - 1)
        if f < nf - 1:
            yb = y + wh
            d.fill(x1 + 1, yb, z1 + 1, x2 - 1, yb, z2 - 1, S["floor"] if d.pack != "Neoterra" else "smooth_stone")
            for x in range(x1, x2 + 1):
                for z in (z1, z2):
                    d.set(x, yb, z, wallblock(d, S["band"], "n" if z == z1 else "s"))
            for z in range(z1, z2 + 1):
                for x in (x1, x2):
                    d.set(x, yb, z, wallblock(d, S["band"], "w"))
    # plinth
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, Y0, z, S["base"] if not (d.pack == "Cascadia" and (x * 7 + z) % 5 == 0) else "mossy_cobblestone")
    # timber framing on Hearthwood upper storeys
    if d.pack == "Hearthwood":
        for f, y in enumerate(ys):
            m = mat if f == 0 else up
            if m in ("calcite", "yellow_terracotta", "white_terracotta", "pink_terracotta", "light_blue_terracotta"):
                framing(d, x1, z1, x2, z2, y, y + wh - 1, S["post"], every=3)
    # corner posts / quoins
    for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        for y in range(Y0, top + 1):
            if d.pack == "Hearthwood":
                if mat == up or y < ys[0] + wh:
                    d.set(x, y, z, ("smooth_stone" if y % 2 else "chiseled_stone_bricks") if mat == "stone_bricks" else
                          ("cut_sandstone" if y % 2 else "chiseled_sandstone") if mat == "smooth_sandstone" else
                          ("smooth_stone" if y % 2 else "stone_bricks"))
                else:
                    d.set(x, y, z, log(S["post"]))
            elif d.pack == "Cascadia":
                d.set(x, y, z, log(S["post"]))
            else:
                d.set(x, y, z, "light_gray_concrete")
    # windows
    sides = {"n": (z1, "x"), "s": (z2, "x"), "w": (x1, "z"), "e": (x2, "z")}
    for f, y in enumerate(ys):
        for sd in win:
            line, along = sides[sd]
            a1, a2 = (x1, x2) if along == "x" else (z1, z2)
            n = a2 - a1 - 3
            if n < 1:
                continue
            for a in range(a1 + 2, a2 - 1):
                if glassy:
                    if (a - a1) % 4 == 0:
                        continue
                elif (a - a1 - 2) % ws != 0:
                    continue
                x, z = (a, line) if along == "x" else (line, a)
                h2 = wh - 1 if glassy or d.pack == "Neoterra" else 2
                for yy in range(y + 1, y + 1 + h2):
                    d.set(x, yy, z, S["glass"] if d.pack != "Neoterra" or f == 0 else "light_gray_stained_glass_pane"
                          if glassy else S["glass"])
                if not deco:
                    continue
                ox, oz = D4[OUT[sd]]
                if d.pack == "Neoterra":
                    if not glassy:
                        put(d, x + ox, y + wh - 1 + 1, z + oz, slab("smooth_quartz_slab", "top")) if False else None
                    continue
                if f == 0:                                          # ground floor: hood moulding only (keeps the
                    put(d, x + ox, y + 3, z + oz, st(f"{S['wood']}_stairs" if d.pack == "Cascadia" else  # pavement free)
                                                    "stone_brick_stairs", OPP[OUT[sd]], "top"))
                    continue
                put(d, x + ox, y, z + oz, f"{S['sill']}[facing={OUT[sd]},half=top,open=false,powered=false,waterlogged=false]")
                if d.pack == "Hearthwood":
                    put(d, x + ox, y + 1, z + oz, "potted_" + S["flowers"][(x + z) % 4])
                lx, lz = D4[CW[OUT[sd]]]
                for s in (1, -1):
                    for yy in range(y + 1, y + 3):
                        put(d, x + lx * s + ox, yy, z + lz * s + oz,
                            f"{S['shutter']}[facing={OUT[sd]},half=bottom,open=true,powered=false,waterlogged=false]")
    # roof
    ridge = top
    if roof == "gable":
        ridge = d.gable(x1, z1, x2, z2, top + 1, axis, f"{S['roof']}_stairs",
                        f"{S['roof']}_slab", gable_end or (up if d.pack != "Cascadia" else "spruce_planks"), overhang=1)
        # gable-end detail: king post (HW) / board and batten (CS), small window
        ends = ((x1, (z1 + z2) // 2), (x2, (z1 + z2) // 2)) if axis == "x" else (((x1 + x2) // 2, z1), ((x1 + x2) // 2, z2))
        for ex, ez in ends:
            for yy in range(top + 1, ridge):
                if d.pack == "Hearthwood" and not d.get(ex, yy, ez).endswith("stairs]") and "stairs" not in d.get(ex, yy, ez):
                    d.set(ex, yy, ez, log(S["post"]))
            if ridge - top >= 4:
                d.set(ex, top + 2, ez, S["glass"])
        if d.pack == "Cascadia":
            for yy in range(top + 1, ridge):
                for a in range((x1 if axis == "z" else z1), (x2 if axis == "z" else z2) + 1):
                    for e in ((z1, z2) if axis == "z" else (x1, x2)):
                        x, z = (a, e) if axis == "z" else (e, a)
                        if d.get(x, yy, z) == "minecraft:spruce_planks" and a % 2 == 0:
                            d.set(x, yy, z, log("stripped_spruce_log"))
        # eave brackets under the overhang on the long sides
        if deco:
            if axis == "x":
                for x in range(x1, x2 + 1, 2):
                    put(d, x, top, z1 - 1, st(f"{S['wood']}_stairs", "south", "top"))
                    put(d, x, top, z2 + 1, st(f"{S['wood']}_stairs", "north", "top"))
            else:
                for z in range(z1, z2 + 1, 2):
                    put(d, x1 - 1, top, z, st(f"{S['wood']}_stairs", "east", "top"))
                    put(d, x2 + 1, top, z, st(f"{S['wood']}_stairs", "west", "top"))
        if beams_on:
            beams(d, x1 + 1, x2 - 1, z1 + 1, z2 - 1, top + 1, S["post"] if d.pack != "Neoterra" else "smooth_quartz",
                  every=4, axis="z" if axis == "x" else "x") if False else None
            if axis == "x":
                for x in range(x1 + 2, x2 - 1, 4):
                    for z in range(z1 + 1, z2):
                        d.set(x, top + 1, z, log(S["post"], "z"))
                    d.set(x, top, (z1 + z2) // 2, "lantern[hanging=true,waterlogged=false]")
            else:
                for z in range(z1 + 2, z2 - 1, 4):
                    for x in range(x1 + 1, x2):
                        d.set(x, top + 1, z, log(S["post"], "x"))
                    d.set((x1 + x2) // 2, top, z, "lantern[hanging=true,waterlogged=false]")
    elif roof == "hip":
        ridge = d.hip(x1, z1, x2, z2, top + 1, f"{S['roof']}_stairs", f"{S['roof']}_slab", overhang=1)
        for x in range(x1 + 2, x2 - 1, 4):
            for z in range(z1 + 2, z2 - 1, 4):
                d.set(x, top + 1, z, d.S["band"] if d.pack != "Cascadia" else "spruce_planks")
                d.set(x, top, z, "lantern[hanging=true,waterlogged=false]")
    else:
        d.fill(x1, top + 1, z1, x2, top + 1, z2, "smooth_quartz" if d.pack == "Neoterra" else S["band"])
        if parapet:
            for x in range(x1, x2 + 1):
                for z in range(z1, z2 + 1):
                    if x in (x1, x2) or z in (z1, z2):
                        d.set(x, top + 2, z, "white_concrete" if d.pack == "Neoterra" else S["base"])
                        d.set(x, top + 3, z, slab("smooth_quartz_slab") if d.pack == "Neoterra" else
                              ("stone_brick_slab[type=bottom,waterlogged=false]" if (x + z) % 2 else "stone_bricks"))
        for x in range(x1, x2 + 1):                                 # cantilevered roof edge
            for z in (z1 - 1, z2 + 1):
                put(d, x, top + 1, z, slab("smooth_quartz_slab", "top") if d.pack == "Neoterra" else slab("stone_brick_slab", "top"))
        for z in range(z1, z2 + 1):
            for x in (x1 - 1, x2 + 1):
                put(d, x, top + 1, z, slab("smooth_quartz_slab", "top") if d.pack == "Neoterra" else slab("stone_brick_slab", "top"))
        for x in range(x1 + 2, x2 - 1, 4):
            for z in range(z1 + 2, z2 - 1, 4):
                d.set(x, top + 1, z, "sea_lantern" if d.pack == "Neoterra" else "glowstone")
        ridge = top + 1
    return dict(ys=ys, top=top, ridge=ridge, x1=x1, z1=z1, x2=x2, z2=z2)


def ext_door(d, x, y, z, facing, wood=None, double=False, along="x", step=True, lamp=True):
    """Exterior door in a wall; facing = the inside direction (doors face into the room as in hm)."""
    wood = wood or d.S["wood"]
    if double:
        d.double_door(x, y, z, along, facing, wood)
    else:
        d.door(x, y, z, facing, wood)
    ox, oz = D4[OPP[facing]]
    cells = [(x, z)] + ([(x + (1 if along == "x" else 0), z + (1 if along == "z" else 0))] if double else [])
    for cx, cz in cells:
        for k in range(3):
            for sgn in (1, -1):
                if d.bp.inside(cx + ox * sgn, y + k, cz + oz * sgn):
                    d.set(cx + ox * sgn, y + k, cz + oz * sgn, AIR)
        keep(d, cx + ox, y, cz + oz, 3)
        keep(d, cx - ox, y, cz - oz, 3)
        d.set(cx + ox, 1, cz + oz, d.S["base"] if d.pack != "Cascadia" else "spruce_planks")
    if lamp:
        lx, lz = D4[CW[facing]]
        far = cells[-1]
        put(d, x - lx + ox, y + 2, z - lz + oz, "lantern[hanging=false,waterlogged=false]") if False else None
        wt = OPP[facing]
        for (cx, cz), s in ((cells[0], -1), (far, 1)):
            px, pz = cx + lx * s, cz + lz * s
            if d.get(px, y + 2, pz) not in (AIR,) and not d.get(px, y + 2, pz).endswith("pane"):
                put(d, px + ox, y + 2, pz + oz, f"wall_torch[facing={wt}]" if d.pack != "Neoterra" else
                    f"end_rod[facing={wt}]")


def link(d, x, y, z, facing, wood=None):
    """Interior door through a wall cell (facing = direction of travel into the next room)."""
    wood = wood or d.S["wood"]
    d.set(x, y, z, AIR)
    d.set(x, y + 1, z, AIR)
    d.door(x, y, z, facing, wood)
    ox, oz = D4[facing]
    for k in range(3):
        for sgn in (1, -1):
            d.set(x + ox * sgn, y + k, z + oz * sgn, AIR)
    keep(d, x + ox, y, z + oz, 3)
    keep(d, x - ox, y, z - oz, 3)
    keep(d, x, y, z, 2)


def arch(d, x, y, z, facing, h=3):
    """Open archway (no door) through a wall cell."""
    for k in range(h):
        d.set(x, y + k, z, AIR)
    ox, oz = D4[facing]
    keep(d, x + ox, y, z + oz, 3)
    keep(d, x - ox, y, z - oz, 3)
    keep(d, x, y, z, 3)


def stair_up(d, x, z, y0, yU, rise, block=None, rails=True):
    """Flight between storeys, reserving the approach and landing; railings on the upper floor along the hole."""
    block = block or (f"{d.S['wood']}_stairs" if d.pack != "Neoterra" else "smooth_quartz_stairs")
    dx, dz = D4[rise]
    n = yU - y0
    keep(d, x - dx, y0, z - dz, 3)
    lx, lz = flight(d, x, z, y0, yU, rise, block, under=d.S["floor"] if d.pack != "Neoterra" else "smooth_quartz")
    keep(d, lx, yU, lz, 3)
    for i in range(n):
        keep(d, x + dx * i, y0 + i + 1, z + dz * i, 3)
    for i in range(max(0, n - 4), n):
        keep(d, x + dx * i, yU, z + dz * i, 2)
    if rails:
        sx, sz = D4[CW[rise]]
        fence = f"{d.S['wood']}_fence" if d.pack != "Neoterra" else "glass_pane"
        for i in range(max(0, n - 4), n):
            for s in (1, -1):
                cx, cz = x + dx * i + sx * s, z + dz * i + sz * s
                if d.bp.inside(cx, yU - 1, cz) and d.get(cx, yU - 1, cz) != AIR and d.air(cx, yU, cz):
                    put(d, cx, yU, cz, fence)
    return lx, lz


# ------------------------------------------------------------------------------------------------ furnishers
def R(x1, z1, x2, z2):
    return (x1, z1, x2, z2)


def wall_cells(r, side, inset=0):
    x1, z1, x2, z2 = r
    if side == "n":
        return [(x, z1 + inset) for x in range(x1, x2 + 1)]
    if side == "s":
        return [(x, z2 - inset) for x in range(x1, x2 + 1)]
    if side == "w":
        return [(x1 + inset, z) for z in range(z1, z2 + 1)]
    return [(x2 - inset, z) for z in range(z1, z2 + 1)]


def mid(r):
    return (r[0] + r[2]) // 2, (r[1] + r[3]) // 2


def pendant(d, x, y, z, h=4):
    """One ceiling light: lantern hanging under the ceiling (glowing panel in Neoterra ceilings)."""
    if d.pack == "Neoterra" and d.get(x, y + h, z) != AIR:
        d.set(x, y + h, z, "sea_lantern")
    elif d.get(x, y + h, z) != AIR:
        put(d, x, y + h - 1, z, "lantern[hanging=true,waterlogged=false]")
    else:
        put(d, x, y + h - 1, z, "lantern[hanging=false,waterlogged=false]") if False else None


def lights(d, r, y, h=4):
    """Ceiling lights at fixed points: the room centre, or the two quarter points of a long room."""
    x1, z1, x2, z2 = r
    cx, cz = mid(r)
    if x2 - x1 >= 10:
        pts = [(x1 + (x2 - x1) // 4, cz), (x2 - (x2 - x1) // 4, cz)]
    elif z2 - z1 >= 10:
        pts = [(cx, z1 + (z2 - z1) // 4), (cx, z2 - (z2 - z1) // 4)]
    else:
        pts = [(cx, cz)]
    for x, z in pts:
        pendant(d, x, y, z, h)


def rug_in(d, r, y, colors=None, inset=1, pattern="border"):
    """A rug centred in the room: 3 wide, up to 5 long along the room's long axis."""
    x1, z1, x2, z2 = r
    cx, cz = mid(r)
    c = colors or d.S["rug"]
    if x2 - x1 >= z2 - z1:
        rx1, rx2, rz1, rz2 = cx - min(2, (x2 - x1) // 2 - inset), cx + min(2, (x2 - x1) // 2 - inset), cz - 1, cz + 1
    else:
        rx1, rx2, rz1, rz2 = cx - 1, cx + 1, cz - min(2, (z2 - z1) // 2 - inset), cz + min(2, (z2 - z1) // 2 - inset)
    for x in range(rx1, rx2 + 1):
        for z in range(rz1, rz2 + 1):
            k = 0 if pattern == "plain" or x in (rx1, rx2) or z in (rz1, rz2) else 1
            put(d, x, y, z, c[k % len(c)])


def banner_at(d, x, y, z, facing, color):
    """Wall banner hung on a solid wall cell behind (x,y,z)."""
    bx, bz = D4[OPP[facing]]
    behind = d.get(x + bx, y, z + bz)
    if behind == AIR or "pane" in behind or "door" in behind or "glass" in behind:
        return
    put(d, x, y, z, f"{color}_wall_banner[facing={facing}]")


def wall_art(d, r, y, sides="nesw", colors=("red", "blue")):
    """Wall decoration at fixed spots: a banner in the middle of each listed wall."""
    x1, z1, x2, z2 = r
    cx, cz = mid(r)
    spots = {"n": (cx, z1, "south"), "s": (cx, z2, "north"), "w": (x1, cz, "east"), "e": (x2, cz, "west")}
    for i, sd in enumerate(sides):
        x, z, f = spots[sd]
        banner_at(d, x, y + 2, z, f, colors[i % len(colors)])


def corners(d, r, y, blocks=None):
    x1, z1, x2, z2 = r
    blocks = blocks or ["potted_" + f for f in d.S["flowers"]]
    for i, (x, z) in enumerate(((x1, z1), (x2, z1), (x1, z2), (x2, z2))):
        put(d, x, y, z, blocks[i % len(blocks)] if not blocks[i % len(blocks)].startswith("potted_cactus")
            else "potted_cactus")


def shelf_wall(d, r, side, y, h=3, chisel=True, skip=()):
    """Book wall: bookshelves (counted), chiseled bookshelves every 4th column for variety."""
    x1, z1, x2, z2 = r
    face = OPP[OUT[side]]
    for k, (x, z) in enumerate(wall_cells(r, side)):
        if (x, z) in skip:
            continue
        for yy in range(y, y + h):
            if (x, yy, z) in d.res or not d.air(x, yy, z):
                continue
            if chisel and k % 4 == 3 and yy == y + 1:
                d.set(x, yy, z, f"chiseled_bookshelf[facing={face},slot_0_occupied=true,slot_1_occupied=true,"
                                f"slot_2_occupied=false,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")
            else:
                d.bookshelf(x, yy, z)


def desk(d, x, y, z, chair_side, wood=None, sit=True, deco="candle"):
    wood = wood or d.S["wood"]
    if not put(d, x, y, z, slab(f"{wood}_slab", "top") if d.pack != "Neoterra" else slab("smooth_quartz_slab", "top")):
        return
    ox, oz = D4[chair_side]
    if d.air(x + ox, y, z + oz) and (x + ox, y, z + oz) not in d.res:
        d.chair(x + ox, y, z + oz, chair_side, wood, sit=sit)
    if deco == "candle":
        put(d, x, y + 1, z, "candle[candles=2,lit=false,waterlogged=false]")
    elif deco:
        put(d, x, y + 1, z, deco)


def office(d, r, y, h=4, desk_side="n"):
    """Study / office: desk pair with chair facing the room, book cases flanking the desk, a rug, two armchairs
    by the window wall, plants and a pendant lamp."""
    x1, z1, x2, z2 = r
    cx, cz = mid(r)
    wz, fz, back = (z1, z1 + 1, "north") if desk_side == "n" else (z2, z2 - 1, "south")
    oz = z2 if desk_side == "n" else z1
    desk(d, cx, y, fz, OPP[back] if False else ("south" if desk_side == "n" else "north"), deco="candle")
    desk(d, cx + 1, y, fz, ("south" if desk_side == "n" else "north"), sit=False, deco="flower_pot")
    for x in (cx - 2, cx - 1, cx + 2, cx + 3):                       # book cases either side of the desk
        if x1 <= x <= x2:
            for k in range(2):
                if d.air(x, y + k, wz + (1 if desk_side == "n" else -1)) and (x, y + k, fz) not in d.res:
                    d.bookshelf(x, y + k, fz)
    for x, b in ((x1, "west"), (x2, "east")):                         # armchairs facing each other
        if d.air(x, y, oz) and (x, y, oz) not in d.res:
            d.chair(x, y, oz, b, d.S["wood"], sit=False)
    put(d, cx, y, oz, f"{d.S['wood']}_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    put(d, cx, y + 1, oz, "potted_" + d.S["flowers"][2] if d.S["flowers"][2] != "white_tulip" else "potted_white_tulip")
    rug_in(d, r, y)
    corners(d, r, y)
    wall_art(d, r, y, "ew")
    lights(d, r, y, h)


def dorm(d, r, y, n, h=4, head="w", color=None, desks=True):
    """Bedroom row: beds with their heads to one wall and a nightstand (slab + candle) after each; a wardrobe pair
    and a writing desk in the middle of the opposite wall."""
    x1, z1, x2, z2 = r
    color = color or d.S["bed"]
    placed = 0
    stand = slab(f"{d.S['wood']}_slab", "top") if d.pack != "Neoterra" else "white_concrete"
    light = "candle[candles=1,lit=false,waterlogged=false]" if d.pack != "Neoterra" else "lantern[hanging=false,waterlogged=false]"
    if head in ("w", "e"):
        hx, step = (x1, 1) if head == "w" else (x2, -1)
        cells = [(hx, z) for z in range(z1, z2 + 1, 2)]
        ox, face = (x2, "west") if head == "w" else (x1, "east")
        cz = (z1 + z2) // 2
        wardrobe = [(ox, cz), (ox, cz + 1)]
        desk_at = (ox, cz - 2)
    else:
        hz, step = (z1, 1) if head == "n" else (z2, -1)
        cells = [(x, hz) for x in range(x1, x2 + 1, 2)]
        oz, face = (z2, "north") if head == "n" else (z1, "south")
        cx = (x1 + x2) // 2
        wardrobe = [(cx, oz), (cx + 1, oz)]
        desk_at = (cx - 2, oz)
    for (x, z) in cells:
        if placed >= n:
            break
        fx, fz = (x + step, z) if head in ("w", "e") else (x, z + step)
        if not (d.air(x, y, z) and d.air(fx, y, fz)) or (x, y, z) in d.res or (fx, y, fz) in d.res:
            continue
        d.bed(x, y, z, OUT[head], color)
        placed += 1
        sx, sz = (x, z + 1) if head in ("w", "e") else (x + 1, z)
        if put(d, sx, y, sz, stand):
            put(d, sx, y + 1, sz, light)
    for i, (x, z) in enumerate(wardrobe):
        put(d, x, y, z, f"chest[facing={face},type={'left' if i == 0 else 'right'},waterlogged=false]")
    if desks:
        desk(d, desk_at[0], y, desk_at[1], face, sit=False, deco="flower_pot")
    rug_in(d, r, y, pattern="plain")
    wall_art(d, r, y, "ns" if head in ("w", "e") else "ew")
    lights(d, r, y, h)
    return placed


def table_set(d, r, y, kind="dining", wood=None, sit=True):
    """Purpose set in the middle of a room: 'dining' (long refectory table, or two in a wide room),
    'meeting' (one conference table), 'study' (reading table with candles and books)."""
    x1, z1, x2, z2 = r
    cx, cz = mid(r)
    wood = wood or d.S["wood"]
    top = "smooth_quartz" if d.pack == "Neoterra" else f"{wood}_planks"
    if x2 - x1 >= z2 - z1:
        ln = max(1, min(6, (x2 - x1) - 4))
        a = cx - ln // 2
        rows = [cz] if (z2 - z1 < 8 or kind != "dining") else [cz - 2, cz + 2]
        for zz in rows:
            if all(d.air(x, y, zz) and (x, y, zz) not in d.res for x in range(a - 1, a + ln + 1)):
                long_table(d, a, zz, a + ln - 1, y, wood, sit=sit, top=top)
    else:
        ln = max(1, min(6, (z2 - z1) - 4))
        a = cz - ln // 2
        cols = [cx] if (x2 - x1 < 8 or kind != "dining") else [cx - 2, cx + 2]
        for xx in cols:
            if all(d.air(xx, y, z) and (xx, y, z) not in d.res for z in range(a - 1, a + ln + 1)):
                long_table_z(d, xx, a, a + ln - 1, y, wood, sit=sit, top=top)


def long_table(d, x1, z, x2, y, wood=None, sit=True, top=None, ends=True, deco=True):
    wood = wood or d.S["wood"]
    n = 0
    for x in range(x1, x2 + 1):
        d.table(x, y, z, wood, "block", top or f"{d.S['wood']}_planks" if d.pack != "Neoterra" else top or "smooth_quartz")
        for dz, back in ((-1, "north"), (1, "south")):
            if d.air(x, y, z + dz) and (x, y, z + dz) not in d.res:
                d.chair(x, y, z + dz, back, wood, sit=sit)
                n += 1
        if deco and x % 2 == 0:
            put(d, x, y + 1, z, "candle[candles=3,lit=false,waterlogged=false]" if x % 4 == 0 else "flower_pot")
    if ends:
        for x, back in ((x1 - 1, "west"), (x2 + 1, "east")):
            if d.air(x, y, z) and (x, y, z) not in d.res:
                d.chair(x, y, z, back, wood, sit=sit)
                n += 1
    return n


def long_table_z(d, x, z1, z2, y, wood=None, sit=True, top=None):
    wood = wood or d.S["wood"]
    n = 0
    for z in range(z1, z2 + 1):
        d.table(x, y, z, wood, "block", top or (f"{wood}_planks" if d.pack != "Neoterra" else "smooth_quartz"))
        for dx, back in ((-1, "west"), (1, "east")):
            if d.air(x + dx, y, z) and (x + dx, y, z) not in d.res:
                d.chair(x + dx, y, z, back, wood, sit=sit)
                n += 1
        if z % 3 == 0:
            put(d, x, y + 1, z, "candle[candles=3,lit=false,waterlogged=false]")
    return n


def classroom(d, r, y, board="n", need=None, wood=None, teacher_spot=False, h=4):
    """Board on one wall, teacher's desk in front, rows of desk+chair facing it, shelves at the back."""
    x1, z1, x2, z2 = r
    wood = wood or d.S["wood"]
    bb = "black_concrete" if d.pack != "Neoterra" else "gray_concrete"
    top = f"{wood}_slab" if d.pack != "Neoterra" else "smooth_quartz_slab"
    n = 0
    if board in ("n", "s"):
        bz = z1 if board == "n" else z2
        cx = (x1 + x2) // 2
        blackboard(d, cx - 2, bz, cx + 2, bz, y + 1, OPP[OUT[board]], bb, wood if d.pack != "Neoterra" else "birch")
        tz = bz + (2 if board == "n" else -2)
        put(d, cx, y, tz, slab(top, "top"))
        put(d, cx + 1, y, tz, slab(top, "top"))
        put(d, cx + 1, y + 1, tz, "candle[candles=1,lit=false,waterlogged=false]")
        sz = bz + (1 if board == "n" else -1)
        if teacher_spot:
            d.spot(cx, y, sz, "work")
            keep(d, cx, y, sz)
        d.chair(cx + 1, y, sz, OUT[board], wood, sit=False)
        n += desk_rows(d, x1 + 1, x2 - 1, (tz + 2) if board == "n" else z1 + 1, z2 - 1 if board == "n" else tz - 2,
                       y, OUT[board], wood, top, every_x=3, need=need)
        shelf_wall(d, (x1, z1, x2, z2), "s" if board == "n" else "n", y, 1, chisel=False)
    else:
        bx = x1 if board == "w" else x2
        cz = (z1 + z2) // 2
        blackboard(d, bx, cz - 2, bx, cz + 2, y + 1, OPP[OUT[board]], bb, wood if d.pack != "Neoterra" else "birch")
        tx = bx + (2 if board == "w" else -2)
        put(d, tx, y, cz, slab(top, "top"))
        put(d, tx, y, cz + 1, slab(top, "top"))
        put(d, tx, y + 1, cz + 1, "candle[candles=1,lit=false,waterlogged=false]")
        sx = bx + (1 if board == "w" else -1)
        if teacher_spot:
            d.spot(sx, y, cz, "work")
            keep(d, sx, y, cz)
        d.chair(sx, y, cz + 1, OUT[board], wood, sit=False)
        n += desk_rows(d, (tx + 2) if board == "w" else x1 + 1, x2 - 1 if board == "w" else tx - 2, z1 + 1, z2 - 1,
                       y, OUT[board], wood, top, every_x=3, need=need)
        shelf_wall(d, (x1, z1, x2, z2), "e" if board == "w" else "w", y, 1, chisel=False)
    corners(d, r, y)
    wall_art(d, r, y, colors=("yellow", "lime", "light_blue"))
    lights(d, r, y, h)
    return n


def lab(d, r, y, h=4, req=()):
    """Laboratory: required work blocks (caller's positions), a central bench with flasks and two stools, a wash
    station of two cauldrons with a specimen shelf between them in the north-west corner."""
    x1, z1, x2, z2 = r
    for it, x, z, f in req:
        if it == "water_cauldron":
            d.item(x, y, z, "water_cauldron[level=3]")
        else:
            d.item(x, y, z, it, f)
    bench_top = "smooth_stone_slab" if d.pack != "Neoterra" else "smooth_quartz_slab"
    cx, cz = mid(r)
    for i, x in enumerate((cx - 1, cx, cx + 1)):
        if put(d, x, y, cz, slab(bench_top, "top")):
            put(d, x, y + 1, cz, ("brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]",
                                  "decorated_pot[cracked=false,facing=north,waterlogged=false]",
                                  "candle[candles=3,lit=false,waterlogged=false]")[i])
    for x in (cx - 1, cx + 1):
        if d.air(x, y, cz + 1) and (x, y, cz + 1) not in d.res:
            d.chair(x, y, cz + 1, "south", d.S["wood"], sit=False)
    put(d, x1 + 1, y, z1, "cauldron")
    if put(d, x1 + 2, y, z1, slab(bench_top, "top")):
        put(d, x1 + 2, y + 1, z1, "potted_red_mushroom")
    put(d, x1 + 3, y, z1, "cauldron")
    corners(d, r, y, ["potted_fern", "potted_dead_bush"])
    lights(d, r, y, h)


def lecture(d, r, y, front="w", need=None, h=4, lectern=False):
    """Lecture hall: benches in rows facing the front wall with a lectern platform and a board."""
    x1, z1, x2, z2 = r
    wood = d.S["wood"]
    bb = "black_concrete" if d.pack != "Neoterra" else "gray_concrete"
    n = 0
    if front in ("w", "e"):
        fx = x1 if front == "w" else x2
        cz = (z1 + z2) // 2
        blackboard(d, fx, cz - 2, fx, cz + 2, y + 1, OPP[OUT[front]], bb, wood if d.pack != "Neoterra" else "birch")
        lx = fx + (2 if front == "w" else -2)
        if lectern:
            d.item(lx, y, cz, "lectern", OPP[OUT[front]] if False else OUT[OPP[front[0]]] if False else
                   ("east" if front == "w" else "west"))
            keep(d, lx + (1 if front == "w" else -1), y, cz)
        else:
            put(d, lx, y, cz, f"{wood}_planks" if d.pack != "Neoterra" else "smooth_quartz")
        rng = range(lx + 3, x2, 2) if front == "w" else range(lx - 3, x1, -2)
        for x in rng:
            for z in range(z1, z2 + 1):
                if z == cz:
                    continue
                if need is not None and n >= need:
                    break
                if d.air(x, y, z) and (x, y, z) not in d.res:
                    d.chair(x, y, z, OUT[OPP[front][0]] if False else ("east" if front == "w" else "west"), wood)
                    n += 1
    else:
        fz = z1 if front == "n" else z2
        cx = (x1 + x2) // 2
        blackboard(d, cx - 2, fz, cx + 2, fz, y + 1, OPP[OUT[front]], bb, wood if d.pack != "Neoterra" else "birch")
        lz = fz + (2 if front == "n" else -2)
        if lectern:
            d.item(cx, y, lz, "lectern", "south" if front == "n" else "north")
            keep(d, cx, y, lz + (1 if front == "n" else -1))
        else:
            put(d, cx, y, lz, f"{wood}_planks" if d.pack != "Neoterra" else "smooth_quartz")
        rng = range(lz + 3, z2, 2) if front == "n" else range(lz - 3, z1, -2)
        for z in rng:
            for x in range(x1, x2 + 1):
                if x == cx:
                    continue
                if need is not None and n >= need:
                    break
                if d.air(x, y, z) and (x, y, z) not in d.res:
                    d.chair(x, y, z, "south" if front == "n" else "north", wood)
                    n += 1
    wall_art(d, r, y, colors=("blue", "white"))
    lights(d, r, y, h)
    return n


def store(d, r, y, h=2, aisle="z"):
    """Store room: two shelving bays of barrels (3 long, 2 high) on each long wall with a sack pile between."""
    x1, z1, x2, z2 = r
    if aisle == "z":
        bays = [((x1, z), "east") for z in (z1, z1 + 1, z1 + 2, z2 - 2, z2 - 1, z2)] + \
               [((x2, z), "west") for z in (z1, z1 + 1, z1 + 2, z2 - 2, z2 - 1, z2)]
        sacks = [(x1, (z1 + z2) // 2), (x2, (z1 + z2) // 2)]
    else:
        bays = [((x, z1), "south") for x in (x1, x1 + 1, x1 + 2, x2 - 2, x2 - 1, x2)] + \
               [((x, z2), "north") for x in (x1, x1 + 1, x1 + 2, x2 - 2, x2 - 1, x2)]
        sacks = [((x1 + x2) // 2, z1), ((x1 + x2) // 2, z2)]
    for (x, z), f in bays:
        if (x, y, z) in d.res or not d.air(x, y, z):
            continue
        d.set(x, y, z, f"barrel[facing={f},open=false]")
        if h > 1 and d.air(x, y + 1, z) and (x, y + 1, z) not in d.res:
            d.set(x, y + 1, z, f"barrel[facing={f},open=false]")
    for x, z in sacks:
        if put(d, x, y, z, "white_wool"):
            put(d, x, y + 1, z, "brown_wool")
    lights(d, r, y, 4)


def workshop(d, r, y, h=4):
    """Workshop: three work stations against the north wall (crafting / smithing / fletching), a tool wall of
    open trapdoors above them, a workbench in the middle with a grindstone at its end."""
    x1, z1, x2, z2 = r
    for x, b in ((x1 + 1, "crafting_table"), (x1 + 3, "smithing_table"), (x1 + 5, "fletching_table")):
        if x <= x2 and (x, y, z1) not in d.res and d.air(x, y, z1) and (x, y, z1 + 1) not in d.res:
            d.set(x, y, z1, b)
            keep(d, x, y, z1 + 1)
            put(d, x, y + 2, z1, f"{d.S['wood']}_trapdoor[facing=south,half=bottom,open=true,powered=false,waterlogged=false]")
    cx, cz = mid(r)
    top = slab(f"{d.S['wood']}_slab" if d.pack != "Neoterra" else "smooth_quartz_slab", "top")
    for i, x in enumerate((cx - 1, cx, cx + 1)):
        if put(d, x, y, cz, top):
            put(d, x, y + 1, cz, ("flower_pot", "candle[candles=2,lit=false,waterlogged=false]", AIR)[i]) if i < 2 else None
    put(d, cx + 2, y, cz, "grindstone[face=floor,facing=east]") if (cx + 3, y, cz) not in d.res and d.air(cx + 3, y, cz) else None
    lights(d, r, y, h)


def kitchen(d, r, y, h=4):
    """Kitchen: a counter run on the north wall (stove, worktop, sink, worktop, oven) and a prep table."""
    x1, z1, x2, z2 = r
    top = "smooth_stone_slab" if d.pack != "Neoterra" else "smooth_quartz_slab"
    run = ["smoker[facing=south,lit=true]", slab(top, "top"), "water_cauldron[level=3]", slab(top, "top"),
           "furnace[facing=south,lit=false]"]
    for i, b in enumerate(run):
        x = x1 + 1 + i
        if x > x2 or (x, y, z1) in d.res or not d.air(x, y, z1):
            continue
        d.set(x, y, z1, b)
        keep(d, x, y, z1 + 1)
        if "slab" in b:
            put(d, x, y + 1, z1, ("flower_pot", "candle[candles=1,lit=false,waterlogged=false]")[i % 2 == 1])
    cx, cz = mid(r)
    if z2 - z1 >= 4:
        for i, x in enumerate((cx, cx + 1)):
            if put(d, x, y, cz + 1, f"{d.S['wood']}_planks" if d.pack != "Neoterra" else "smooth_quartz"):
                put(d, x, y + 1, cz + 1, ("cake[bites=0]", "flower_pot")[i])
    lights(d, r, y, h)


def ward(d, r, y, n, head=("n", "s"), h=4, color="white"):
    x1, z1, x2, z2 = r
    placed = 0
    if n <= 0:                                                       # no patients here yet: a day room
        lounge(d, r, y, h)
        desk(d, x1 + 1, y, z1, "south", sit=False, deco="flower_pot")
        return 0
    for hd in head:
        if placed >= n:
            break
        if hd in ("n", "s"):
            placed += ward_row(d, x1, x2, z1 if hd == "n" else z2, y, OUT[hd], color, n - placed)
        else:
            placed += ward_col(d, x1 if hd == "w" else x2, z1, z2, y, OUT[hd], color, n - placed)
    rug_in(d, r, y, ("white_carpet",) if d.pack != "Cascadia" else ("green_carpet",), inset=2, pattern="plain")
    lights(d, r, y, h)
    return placed


def lounge(d, r, y, h=4):
    """Sitting room: two sofas facing each other across a coffee table with a plant, a rug, side plants."""
    x1, z1, x2, z2 = r
    wood = d.S["wood"]
    cx, cz = mid(r)
    for x in range(cx - 1, cx + 2):
        if d.air(x, y, cz - 1) and (x, y, cz - 1) not in d.res:
            d.chair(x, y, cz - 1, "north", wood)
        if d.air(x, y, cz + 1) and (x, y, cz + 1) not in d.res:
            d.chair(x, y, cz + 1, "south", wood)
    put(d, cx, y, cz, f"{wood}_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    put(d, cx, y + 1, cz, "potted_" + d.S["flowers"][1])
    rug_in(d, r, y)
    corners(d, r, y)
    wall_art(d, r, y, "ew")
    lights(d, r, y, h)


def lawn(d, x1, z1, x2, z2, mat="grass_block[snowy=false]"):
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if d.get(x, 1, z) != AIR and d.air(x, 2, z):
                d.set(x, 1, z, mat)


def path(d, x1, z1, x2, z2, mat=None, border=True):
    mat = mat or d.S["path"]
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for z in range(min(z1, z2), max(z1, z2) + 1):
            d.set(x, 1, z, mat)
    if border:
        b = {"Hearthwood": "stone_bricks", "Cascadia": "cobblestone", "Neoterra": "polished_andesite"}[d.pack]
        if x1 == x2 or z1 == z2 or True:
            for x in range(min(x1, x2) - 1, max(x1, x2) + 2):
                for z in range(min(z1, z2) - 1, max(z1, z2) + 2):
                    if (x < min(x1, x2) or x > max(x1, x2) or z < min(z1, z2) or z > max(z1, z2)) and \
                            d.bp.inside(x, 1, z) and d.get(x, 1, z).startswith("minecraft:grass_block"):
                        d.set(x, 1, z, b)


def flowerbed(d, x1, z1, x2, z2, flowers=None):
    flowers = flowers or ("poppy", "dandelion", "azure_bluet", "oxeye_daisy", "cornflower", "allium")
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for z in range(min(z1, z2), max(z1, z2) + 1):
            if d.air(x, 2, z) and (x, 2, z) not in d.res:
                d.set(x, 1, z, "grass_block[snowy=false]")
                d.set(x, 2, z, flowers[(x * 3 + z) % len(flowers)])


def hedge(d, x1, z1, x2, z2, leaves="oak_leaves"):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for z in range(min(z1, z2), max(z1, z2) + 1):
            put(d, x, 2, z, f"{leaves}[distance=1,persistent=true,waterlogged=false]")


def post_lamp(d, x, z, kind=None):
    if d.pack == "Neoterra":
        put(d, x, 2, z, "light_gray_concrete_powder") if False else None
        for k, b in enumerate(("birch_fence", "birch_fence", "birch_fence", "sea_lantern")):
            put(d, x, 2 + k, z, b)
    elif d.pack == "Hearthwood":
        for k, b in enumerate(("stone_brick_wall", "dark_oak_fence", "dark_oak_fence", "lantern[hanging=false,waterlogged=false]")):
            put(d, x, 2 + k, z, b)
    else:
        for k, b in enumerate(("spruce_log[axis=y]", "spruce_fence", "spruce_fence", "lantern[hanging=false,waterlogged=false]")):
            put(d, x, 2 + k, z, b)


def park_bench(d, x, z, along, back, tag=None):
    wood = d.S["wood"]
    dx, dz = (1, 0) if along == "x" else (0, 1)
    for k in range(2):
        cx, cz = x + dx * k, z + dz * k
        if d.air(cx, 2, cz) and (cx, 2, cz) not in d.res:
            d.chair(cx, 2, cz, back, wood, sit=(tag == "sit"))
            if tag and tag != "sit":
                d.tag(cx, 2, cz, tag)
    for s in (-1, 2):
        put(d, x + dx * s, 2, z + dz * s, f"{wood}_trapdoor[facing={back},half=bottom,open=true,powered=false,waterlogged=false]") if False else None


def plant_tree(d, x, z, kind=None):
    kind = kind or {"Hearthwood": "oak", "Cascadia": "spruce", "Neoterra": "birch"}[d.pack]
    if not d.air(x, 2, z):
        return
    d.set(x, 1, z, "grass_block[snowy=false]")
    if kind == "spruce":
        h = 6
        for k in range(h):
            d.set(x, 2 + k, z, log("spruce_log"))
        for y, r in ((4, 2), (5, 1), (6, 2), (7, 1), (8, 0)):
            for a in range(-r, r + 1):
                for b in range(-r, r + 1):
                    if abs(a) + abs(b) <= r + (1 if r == 2 else 0) and d.air(x + a, y, z + b):
                        put(d, x + a, y, z + b, "spruce_leaves[distance=1,persistent=true,waterlogged=false]")
        put(d, x, 8, z, "spruce_leaves[distance=1,persistent=true,waterlogged=false]")
    else:
        tree(d, x, 2, z, f"{kind}_log", f"{kind}_leaves", 4 if kind == "birch" else 5, 2)


def fountain(d, cx, cz, r=2):
    rim = {"Hearthwood": "stone_brick_wall", "Cascadia": "mossy_cobblestone_wall", "Neoterra": "smooth_quartz_slab[type=bottom,waterlogged=false]"}[d.pack]
    for x in range(cx - r, cx + r + 1):
        for z in range(cz - r, cz + r + 1):
            if x in (cx - r, cx + r) or z in (cz - r, cz + r):
                d.set(x, 2, z, rim)
                d.set(x, 1, z, {"Hearthwood": "stone_bricks", "Cascadia": "cobblestone", "Neoterra": "smooth_quartz"}[d.pack])
            else:
                d.set(x, 1, z, "stone_bricks" if d.pack != "Neoterra" else "light_blue_concrete")
                d.set(x, 2, z, "water[level=0]")
    d.set(cx, 2, cz, {"Hearthwood": "stone_bricks", "Cascadia": "mossy_cobblestone", "Neoterra": "smooth_quartz"}[d.pack])
    d.set(cx, 3, cz, {"Hearthwood": "stone_brick_wall", "Cascadia": "mossy_cobblestone_wall", "Neoterra": "end_rod[facing=up]"}[d.pack])
    d.set(cx, 4, cz, "water[level=0]" if d.pack != "Neoterra" else "sea_lantern") if d.pack == "Neoterra" else \
        d.set(cx, 4, cz, "lantern[hanging=false,waterlogged=false]")


def chimney(d, x, z, y1, y2, mat=None):
    mat = mat or {"Hearthwood": "bricks", "Cascadia": "cobblestone", "Neoterra": "light_gray_concrete"}[d.pack]
    for y in range(y1, y2 + 1):
        d.set(x, y, z, mat if not (d.pack == "Cascadia" and y % 3 == 0) else "mossy_cobblestone")
    d.set(x, y2 + 1, z, {"Hearthwood": "brick_wall", "Cascadia": "cobblestone_wall", "Neoterra": "iron_bars"}[d.pack])
    d.set(x, y2 + 2, z, "campfire[facing=north,lit=false,signal_fire=false,waterlogged=false]") if False else None


def cart(d, x, z, along="x"):
    """Hand cart: two wheels (dark trapdoors), bed of slabs, a sack."""
    wood = d.S["wood"] if d.pack != "Neoterra" else "spruce"
    dx, dz = (1, 0) if along == "x" else (0, 1)
    put(d, x, 2, z, slab(f"{wood}_slab", "top"))
    put(d, x + dx, 2, z + dz, slab(f"{wood}_slab", "top"))
    put(d, x, 3, z, "brown_wool") if False else put(d, x + dx, 3, z + dz, "hay_block[axis=y]") if False else None
    put(d, x - dx, 2, z - dz, f"{wood}_fence")
    put(d, x + dx, 3, z + dz, "barrel[facing=up,open=false]") if False else None


def roof_garden(d, b, kind="garden"):
    """Neoterra roof: planters round the edge, solar panels, a vent unit and an antenna."""
    x1, z1, x2, z2, top = b["x1"], b["z1"], b["x2"], b["z2"], b["top"]
    ry = top + 2
    for x in range(x1 + 1, x2):
        for z in (z1 + 1, z2 - 1):
            put(d, x, ry, z, "moss_block" if (x % 4) else "flowering_azalea")
    if kind == "solar":
        for x in range(x1 + 2, x2 - 1):
            for z in range(z1 + 3, z2 - 2):
                if (z - z1) % 3 != 2:
                    put(d, x, ry, z, "daylight_detector[inverted=false,power=0]")
    else:
        for x in range(x1 + 2, x2 - 1, 3):
            for z in range(z1 + 3, z2 - 2, 3):
                put(d, x, ry, z, "potted_bamboo" if (x + z) % 2 else "flowering_azalea")
    put(d, x2 - 2, ry, z1 + 2, "smooth_stone")
    put(d, x2 - 2, ry + 1, z1 + 2, "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    put(d, x1 + 2, ry, z2 - 2, "lightning_rod[facing=up,powered=false,waterlogged=false]")


# ============================================================================================ UNIVERSITY v2
def uni_hearthwood(rel, L):
    """Oxford college growing into a full quadrangle campus."""
    d = new("Hearthwood", rel, (49, 30, 57))
    SB = "stone_bricks"
    # ---- L1: Old Schools – the study (common room) with fireplace, study table, lectern, rack
    os_nf = 2 if L >= 4 else 1
    b = bldg(d, 8, 8, 20, 15, os_nf, "gable", "x", mat=SB, up=SB, gable_end=SB)
    ext_door(d, 14, Y0, 8, "south", double=False)
    d.sign(14, 5, 7, "north", ["OLD SCHOOLS", "", "Collegium"], "dark_oak")
    d.hut(19, Y0, 9)
    keep(d, 18, Y0, 9)
    d.hearth(9, Y0, 12, "east", b["ridge"] + 2, "bricks", "campfire")
    chimney(d, 8, 12, Y0, b["ridge"] + 1)
    d.chair(11, Y0, 11, "west", "dark_oak", arms=False)
    d.chair(11, Y0, 13, "west", "dark_oak", arms=False)
    d.item(19, Y0, 13, "lectern", "west")
    keep(d, 18, Y0, 13)
    d.rack(19, Y0, 11, "west")
    keep(d, 18, Y0, 11)
    d.item(9, Y0, 9, "furnace", "east")
    keep(d, 10, Y0, 9)
    if os_nf == 2:
        stair_up(d, 13, 14, Y0, 7, "east")
    long_table(d, 14, 12, 16, Y0, "dark_oak")
    shelf_wall(d, (9, 9, 19, 14), "s", Y0, 3, skip=[(9, 14), (19, 14)])
    rug_in(d, (9, 9, 19, 14), Y0, ("red_carpet", "brown_carpet"))
    corners(d, (9, 9, 19, 14), Y0)
    wall_art(d, (9, 9, 19, 14), Y0, "n", ("blue", "white"))
    if os_nf == 2:                                                  # upper storey: student sets
        dorm(d, (9, 9, 19, 13), 7, 5, head="n")
    # forecourt
    path(d, 13, 0, 15, 7)
    for x in (11, 17):
        post_lamp(d, x, 5)
    flowerbed(d, 9, 5, 11, 6)
    flowerbed(d, 17, 5, 19, 6)
    # ---- L2: gate tower + laboratory range
    if L >= 2:
        g = bldg(d, 21, 7, 25, 15, 3, "flat", mat=SB, up=SB, win="nesw", ws=2)
        d.clear(22, Y0, 7, 24, 5, 15)                              # gate passage
        for x in range(22, 25):
            for z in range(7, 16):
                d.set(x, 1, z, "stone_bricks")
        for z in (7, 15):
            d.set(22, 5, z, st("stone_brick_stairs", "west", "top"))
            d.set(24, 5, z, st("stone_brick_stairs", "east", "top"))
            d.set(23, 5, z, "chiseled_stone_bricks")
        for x, z in ((21, 7), (25, 7), (21, 15), (25, 15)):        # corner turrets
            for y in range(g["top"] + 2, g["top"] + 5):
                d.set(x, y, z, SB if y < g["top"] + 4 else "stone_brick_wall")
        d.banner(22, 9, 6, "north", "blue")
        d.banner(24, 9, 6, "north", "blue")
        clockface(d, 23, 13, 7, "north", "smooth_quartz")
        for y in range(Y0, g["top"] + 1):                          # ladder up the tower
            d.set(25 - 1, y, 14, "ladder[facing=north,waterlogged=false]") if y >= 6 else None
        office(d, (22, 8, 24, 14), 7)
        shelf_wall(d, (22, 8, 24, 14), "w", 12, 3)
        d.set(23, 12, 11, "dark_oak_slab[type=top,waterlogged=false]")
        # laboratory
        lb_nf = 2 if L >= 4 else 1
        b2 = bldg(d, 26, 8, 38, 15, lb_nf, "gable", "x", mat=SB, up=SB, gable_end=SB)
        ext_door(d, 32, Y0, 8, "south")
        chimney(d, 38, 13, Y0, b2["ridge"] + 1)
        fur = max(0, need(d, "furnace") - 1)
        reqs = [("brewing_stand", 37, 10, None), ("water_cauldron", 37, 11, None), ("crafting_table", 37, 12, None)]
        reqs += [("furnace", 37, 13 + i, "west") if i < 1 else ("furnace", 36, 14, "north") for i in range(fur)]
        for it, x, z, f in reqs:
            keep(d, x - 1, Y0, z) if x == 37 else keep(d, x, Y0, z - 1)
        lab(d, (27, 9, 37, 14), Y0, req=reqs)
        d.sign(32, 5, 7, "north", ["LABORATORY"], "dark_oak")
        if lb_nf == 2:
            stair_up(d, 28, 14, Y0, 7, "east")
            dorm(d, (27, 9, 37, 13), 7, 5, head="n")
        path(d, 31, 0, 33, 7)
        flowerbed(d, 27, 5, 29, 6)
        flowerbed(d, 35, 5, 37, 6)
        post_lamp(d, 30, 5)
        post_lamp(d, 34, 5)
    # ---- L3: great hall (lecture) closes the quad; quad lawn with paths and strollers
    if L >= 3:
        h = bldg(d, 8, 32, 38, 40, 1, "gable", "x", mat=SB, up=SB, gable_end=SB, wh=6)
        for x in (22, 23, 24):                                      # louvre on the ridge
            for z in (35, 36, 37):
                d.set(x, h["ridge"], z, "dark_oak_planks")
        for x, z in ((22, 35), (24, 35), (22, 37), (24, 37)):
            d.set(x, h["ridge"] + 1, z, "dark_oak_fence")
        d.hip(22, 35, 24, 37, h["ridge"] + 2, "deepslate_tile_stairs", "deepslate_tile_slab", overhang=0)
        for x in range(10, 38, 4):                                  # buttresses
            for z, f in ((31, "south"), (41, "north")):
                for y in range(Y0, 6):
                    put(d, x, y, z, SB)
                put(d, x, 6, z, st("stone_brick_stairs", f))
        link(d, 23, Y0, 32, "south")
        lecture(d, (9, 33, 37, 39), Y0, "w", need=None, h=6)
        d.set(10, Y0, 35, "dark_oak_planks") if False else None
        for x in (11,):
            for z in range(33, 40):
                put(d, x, Y0, z, "red_carpet")
        shelf_wall(d, (9, 33, 37, 39), "e", Y0, 3)
        # quad
        lawn(d, 15, 16, 31, 31)
        path(d, 22, 16, 24, 31)
        path(d, 15, 23, 31, 24)
        for x, z in ((20, 23), (26, 23), (23, 19), (23, 28), (18, 24), (28, 24), (23, 17), (23, 30)):
            d.spot(x, Y0, z, "leisure")
            keep(d, x, Y0, z)
        for x, z in ((17, 18), (29, 18), (17, 29), (29, 29)):
            plant_tree(d, x, z)
        for x, z in ((20, 20), (26, 27)):
            park_bench(d, x, z, "x", "north" if z < 24 else "south")
        hedge(d, 15, 31, 21, 31)
        hedge(d, 25, 31, 31, 31)
    # ---- L4: library range (west of the quad), two storeys
    if L >= 4:
        lb = bldg(d, 8, 16, 14, 31, 2, "gable", "z", mat=SB, up=SB, gable_end=SB, ws=2)
        link(d, 14, Y0, 23, "west")
        r1 = (9, 17, 13, 30)
        shelf_wall(d, r1, "w", Y0, 3)
        for z in range(19, 29, 3):
            for x in (11, 12):
                d.bookshelf(x, Y0, z, 2)
        for z in (18, 21, 24, 27):
            desk(d, 13, Y0, z, "west", sit=True)
        stair_up(d, 10, 29, Y0, 7, "north") if False else stair_up(d, 9, 29, Y0, 7, "north") if False else None
        stair_up(d, 13, 30, Y0, 7, "north")
        shelf_wall(d, r1, "w", 7, 3)
        long_table_z(d, 11, 19, 24, 7)
        lights(d, r1, 7)
        rug_in(d, r1, Y0, ("green_carpet",), pattern="plain")
        # cloister arcade along the quad side of the library
        for z in range(16, 32):
            if z % 2:
                for y in range(Y0, 5):
                    put(d, 16, y, z, "stone_brick_wall")
            put(d, 16, 5, z, SB)
            put(d, 15, 5, z, slab("deepslate_tile_slab", "top")) if False else d.set(15, 5, z, slab("stone_brick_slab", "top"))
            d.set(16, 5, z, SB)
    # ---- L5: chapel with bell-cote (east of the quad), kitchen, master's garden, fountain
    if L >= 5:
        c = bldg(d, 32, 16, 38, 31, 1, "gable", "z", mat=SB, up=SB, gable_end=SB, wh=7, ws=2)
        link(d, 32, Y0, 23, "east")
        for z in range(18, 29, 2):                                  # pews
            for x in (34, 36, 37):
                if d.air(x, Y0, z):
                    d.chair(x, Y0, z, "south", "dark_oak")
        d.set(35, Y0, 30, "dark_oak_planks")
        put(d, 35, Y0 + 1, 30, "candle[candles=4,lit=false,waterlogged=false]")
        put(d, 34, Y0, 30, "candle[candles=3,lit=false,waterlogged=false]")
        put(d, 36, Y0, 30, "candle[candles=3,lit=false,waterlogged=false]")
        d.window(35, 4, 31, 35, 7, 31, "purple_stained_glass_pane")
        d.set(35, c["ridge"] + 1, 16, "stone_brick_wall")
        d.set(35, c["ridge"] + 2, 16, "stone_bricks")
        bell(d, 35, c["ridge"] + 1, 17) if False else None
        for x in (34, 36):
            d.set(x, c["ridge"] + 1, 16, "stone_brick_wall")
            d.set(x, c["ridge"] + 2, 16, "stone_brick_slab[type=bottom,waterlogged=false]")
        d.set(35, c["ridge"] + 1, 16, AIR)
        bell(d, 35, c["ridge"] + 1, 16)
        for z in range(18, 30):
            put(d, 35, Y0, z, "red_carpet")
        lights(d, (33, 17, 37, 30), Y0, 7)
        fountain(d, 23, 24, 2)
        for x, z in ((23, 21), (23, 27)):
            pass
        # master's garden west of the Old Schools
        lawn(d, 1, 16, 6, 44)
        for z in range(18, 44, 4):
            flowerbed(d, 2, z, 3, z + 1)
            plant_tree(d, 5, z + 2) if z % 8 == 2 else None
        for z in range(16, 45):
            put(d, 0, 2, z, "dark_oak_fence")
        path(d, 39, 0, 47, 3, border=False)
        for x in range(40, 47, 3):
            cart(d, x, 2)
        # the New Building: three-storey student residence south of the hall, garden between
        nb = bldg(d, 10, 45, 36, 52, 3, "gable", "x", mat=SB, up=SB, gable_end=SB)
        ext_door(d, 23, Y0, 45, "south", double=True)
        arch(d, 23, Y0, 40, "south")
        path(d, 23, 41, 24, 44)
        lawn(d, 8, 41, 38, 44)
        flowerbed(d, 9, 42, 20, 43)
        flowerbed(d, 27, 42, 37, 43)
        stair_up(d, 12, 51, Y0, 7, "east")
        stair_up(d, 33, 51, 7, 12, "west")
        lounge(d, (11, 46, 22, 50), Y0)
        table_set(d, (25, 46, 35, 50), Y0, "dining")
        dorm(d, (11, 46, 35, 50), 7, 10, head="n")
        dorm(d, (11, 46, 35, 50), 12, 10, head="n")
        for x in (14, 32):
            chimney(d, x, 52, Y0 + 1, nb["ridge"] + 1)
    shelf_runs(d, [], 0)
    return d


def uni_neoterra(rel, L):
    """Research campus: pavilion -> lab block & bridge -> lecture theatre & quad -> extra storeys -> dorm tower,
    student union, sports court."""
    d = new("Neoterra", rel, (53, 40, 55), paving="smooth_stone")
    Q = "smooth_quartz"
    pv_nf = 3 if L >= 4 else 1
    p = bldg(d, 6, 6, 18, 14, pv_nf, "flat", glassy=True, win="nsw")
    ext_door(d, 11, Y0, 6, "south", double=True)
    d.sign(12, 6, 5, "north", ["INSTITUTE OF", "SCIENCE"], "birch", glow=True, color="cyan")
    for x in range(9, 16):
        for z in (3, 4, 5):
            put(d, x, 6, z, slab("smooth_quartz_slab", "top"))
    d.hut(7, Y0, 7)
    keep(d, 8, Y0, 7)
    d.item(17, Y0, 7, "lectern", "west")
    keep(d, 16, Y0, 7)
    d.rack(7, Y0, 13, "north")
    keep(d, 7, Y0, 12)
    d.item(17, Y0, 13, "furnace", "west")
    keep(d, 16, Y0, 13)
    if pv_nf > 1:
        stair_up(d, 8, 9, Y0, 7, "south")
        stair_up(d, 16, 12, 7, 12, "north")
    for x in range(10, 15):
        d.table(x, Y0, 10, "birch", "block", Q)
    for x in range(10, 15):
        d.chair(x, Y0, 9, "north", "mangrove")
        d.chair(x, Y0, 11, "south", "mangrove")
    shelf_wall(d, (7, 7, 17, 13), "s", Y0, 3)
    rug_in(d, (9, 8, 15, 12), Y0, ("cyan_carpet",), inset=0, pattern="plain")
    corners(d, (7, 7, 17, 13), Y0, ["potted_bamboo"])
    if pv_nf > 1:
        r2 = (7, 7, 17, 13)
        table_set(d, r2, 7, "dining")
        lights(d, r2, 7)
        office(d, (7, 7, 11, 13), 12)
        office(d, (13, 7, 17, 13), 12, desk_side="s")
        d.fill(12, 12, 7, 12, 15, 13, "light_gray_stained_glass")
        link(d, 12, 12, 10, "east") if False else arch(d, 12, 12, 10, "east")
        roof_garden(d, p, "garden")
    path(d, 10, 0, 13, 5, "smooth_stone")
    for x in (4, 20):
        post_lamp(d, x, 4)
    if L >= 2:
        lb_nf = {2: 1, 3: 1, 4: 2, 5: 3}[L]
        b2 = bldg(d, 26, 6, 40, 14, lb_nf, "flat", glassy=True, win="nse")
        d.box(18, Y0, 8, 26, 5, 12, "glass", floor="polished_diorite")
        d.fill(18, 6, 8, 26, 6, 12, Q)
        d.clear(19, Y0, 9, 25, 5, 11)
        for x in (18, 26):
            arch(d, x, Y0, 10, "east")
        for x in range(19, 26, 2):
            put(d, x, Y0, 9, "potted_bamboo")
            put(d, x, 5, 10, "sea_lantern") if False else d.set(x, 6, 10, "sea_lantern")
        ext_door(d, 33, Y0, 6, "south", double=True)
        d.sign(33, 6, 5, "north", ["LABS"], "birch", glow=True, color="cyan")
        fur = max(0, need(d, "furnace") - 1)
        reqs = [("brewing_stand", 39, 8, None), ("water_cauldron", 39, 9, None), ("crafting_table", 39, 10, None)]
        reqs += [("furnace", 39, 11 + i, "west") for i in range(fur)]
        for it, x, z, f in reqs:
            keep(d, x - 1, Y0, z)
        lab(d, (27, 7, 39, 13), Y0, req=reqs)
        if lb_nf > 1:
            stair_up(d, 28, 13, Y0, 7, "east")
            classroom(d, (27, 7, 39, 12), 7, board="e")
            roof_garden(d, b2, "solar")
        if lb_nf > 2:
            stair_up(d, 38, 13, 7, 12, "west")
            office(d, (27, 7, 32, 13), 12)
            office(d, (34, 7, 39, 13), 12, desk_side="s")
            d.fill(33, 12, 7, 33, 15, 13, "light_gray_stained_glass")
            arch(d, 33, 12, 10, "east")
        for x in (22, 44):
            plant_tree(d, x, 3)
    if L >= 3:
        X1, X2, Z1, Z2 = 14, 38, 38, 47
        bldg(d, X1, Z1, X2, Z2, 1, "flat", wh=8, win="s", ws=4)
        shelf_wall(d, (X1 + 1, Z1 + 1, X2 - 1, Z2 - 1), "w", Y0, 3)
        shelf_wall(d, (X1 + 1, Z1 + 1, X2 - 1, Z2 - 1), "e", Y0, 3)
        for x in range(X1, X2 + 1):
            d.set(x, 9, Z1, "cyan_terracotta")
        ext_door(d, 26, Y0, Z1, "north", double=True)
        for x in range(18, 35):
            d.set(x, 6, Z1 + 1, "black_concrete")
            d.set(x, 7, Z1 + 1, "black_concrete")
        d.set(26, 7, Z1 + 1, "sea_lantern")
        put(d, 20, Y0, Z1 + 2, Q)
        for k in range(3):                                          # raked tiers rising south
            zs = Z1 + 4 + 2 * k
            for z in (zs, zs + 1):
                for x in range(X1 + 1, X2):
                    for y in range(Y0, Y0 + k):
                        d.set(x, y, z, Q)
            for x in range(X1 + 3, X2 - 2):
                if x in (20, 26, 32):
                    continue
                d.chair(x, Y0 + k, zs, "south", "birch")
        lights(d, (X1 + 1, Z1 + 1, X2 - 1, Z2 - 1), Y0, 8)
        lawn(d, 6, 16, 46, 36)
        path(d, 25, 15, 27, 37)
        path(d, 6, 26, 46, 26)
        for x, z in ((12, 26), (18, 26), (34, 26), (40, 26), (26, 19), (26, 23), (26, 30), (26, 34)):
            d.spot(x, Y0, z, "leisure")
            keep(d, x, Y0, z)
        for x, z in ((10, 20), (42, 20), (10, 32), (42, 32), (18, 20), (34, 32)):
            plant_tree(d, x, z)
        for x, z in ((20, 24), (30, 24)):
            park_bench(d, x, z, "x", "north")
        for x, z in ((20, 28), (30, 28)):
            park_bench(d, x, z, "x", "south")
        fountain(d, 26, 26, 2) if L >= 4 else None
    if L >= 4:
        un = bldg(d, 6, 17, 14, 34, 2, "flat", glassy=True, win="nsew")
        ext_door(d, 14, Y0, 25, "west", double=True, along="z")
        kitchen(d, (7, 18, 13, 21), Y0)
        table_set(d, (7, 23, 13, 33), Y0, "dining")
        stair_up(d, 7, 33, Y0, 7, "north")
        lounge(d, (7, 18, 13, 26), 7)
        table_set(d, (7, 27, 13, 33), 7, "dining")
        roof_garden(d, un, "garden")
        d.sign(14, 6, 21, "east", ["STUDENT", "UNION"], "birch", glow=True, color="cyan")
    if L >= 5:
        dt = bldg(d, 38, 17, 46, 34, 6, "flat", glassy=True, win="nsew")
        ext_door(d, 38, Y0, 25, "east")
        for k in range(5):
            stair_up(d, 39 + (k % 2) * 6, 18 if k % 2 == 0 else 33, Y0 + 5 * k, Y0 + 5 * k + 5,
                     "south" if k % 2 == 0 else "north")
        for k in range(6):
            y = Y0 + 5 * k
            if k == 0:
                lounge(d, (39, 19, 45, 32), y)
            else:
                dorm(d, (39, 20, 45, 31), y, 6, head="e")
        roof_garden(d, dt, "solar")
        # sports court beside the street
        for x in range(42, 52):
            for z in range(1, 15):
                edge = x in (42, 51) or z in (1, 14) or z == 8
                d.set(x, 1, z, "white_concrete" if edge else "light_blue_terracotta")
        for z in (2, 13):
            put(d, 46, 2, z, "iron_bars")
            put(d, 46, 3, z, "iron_bars")
            put(d, 46, 4, z, "white_stained_glass")
    return d


def uni_cascadia(rel, L):
    """Timber college: lodges round a quad joined by covered boardwalks."""
    d = new("Cascadia", rel, (53, 30, 55), paving="coarse_dirt")
    st_nf = 2 if L >= 4 else 1
    b = bldg(d, 6, 6, 18, 14, st_nf, "gable", "x")
    ext_door(d, 12, Y0, 6, "south")
    d.fill(5, 1, 2, 19, 1, 5, "spruce_planks")                     # porch
    for x in (5, 19, 9, 15):
        for y in range(Y0, 6):
            put(d, x, y, 2, log("spruce_log"))
    for x in range(4, 21):
        d.set(x, 6, 1, st("spruce_stairs", "south"))
        for z in range(2, 6):
            d.set(x, 6, z, slab("spruce_slab"))
    d.sign(12, 5, 5, "north", ["TIMBERLINE", "COLLEGE"], "spruce")
    d.hut(7, Y0, 7)
    keep(d, 8, Y0, 7)
    d.item(17, Y0, 7, "lectern", "west")
    keep(d, 16, Y0, 7)
    d.rack(7, Y0, 13, "north")
    keep(d, 7, Y0, 12)
    d.item(17, Y0, 13, "furnace", "west")
    keep(d, 16, Y0, 13)
    d.hearth(12, Y0, 13, "north", b["ridge"] + 1, "cobblestone", "campfire")
    chimney(d, 12, 14, Y0, b["ridge"] + 1)
    if st_nf > 1:
        stair_up(d, 16, 8, Y0, 7, "south")
    for x in range(10, 15):
        d.table(x, Y0, 9, "spruce", "block", "stripped_spruce_wood[axis=y]")
        d.chair(x, Y0, 8, "north", "spruce")
        d.chair(x, Y0, 10, "south", "spruce")
    d.chair(11, Y0, 11, "south", "spruce", arms=True) if False else None
    shelf_wall(d, (7, 7, 17, 13), "w", Y0, 3, skip=[(7, 7), (7, 13)])
    shelf_wall(d, (7, 7, 17, 13), "e", Y0, 2, skip=[(17, 7), (17, 13)])
    rug_in(d, (9, 11, 15, 12), Y0, ("brown_carpet",), inset=0, pattern="plain")
    if st_nf > 1:
        dorm(d, (7, 7, 17, 13), 7, 4, head="n")
    if L >= 2:
        c_nf = 1
        b2 = bldg(d, 30, 6, 42, 14, c_nf, "gable", "x")
        ext_door(d, 36, Y0, 6, "south")
        d.sign(36, 5, 5, "north", ["CHEMISTRY"], "spruce")
        chimney(d, 42, 10, Y0, b2["ridge"] + 1)
        fur = max(0, need(d, "furnace") - 1)
        reqs = [("brewing_stand", 41, 8, None), ("water_cauldron", 41, 9, None), ("crafting_table", 41, 10, None)]
        reqs += [("furnace", 41, 11 + i, "west") for i in range(fur)]
        for it, x, z, f in reqs:
            keep(d, x - 1, Y0, z)
        lab(d, (31, 7, 41, 13), Y0, req=reqs)
        shelf_wall(d, (31, 7, 41, 13), "s", Y0, 2, skip=[(31, 13), (41, 13)])
        # covered boardwalk
        for x in range(19, 30):
            for z in range(8, 13):
                d.set(x, 1, z, "spruce_planks")
                d.set(x, 6, z, slab("spruce_slab"))
            for z in (8, 12):
                if x % 3 == 1:
                    for y in range(Y0, 6):
                        d.set(x, y, z, log("spruce_log"))
                else:
                    d.set(x, Y0, z, "spruce_fence")
        for x0 in (18, 30):
            link(d, x0, Y0, 10, "east" if x0 == 18 else "west")
        for x in range(20, 30, 4):
            d.set(x, 5, 10, "lantern[hanging=true,waterlogged=false]")
        for x in (24,):
            d.set(x, Y0, 8, AIR)
            d.set(x, Y0, 12, AIR)
        for x, z in ((22, 3), (27, 3), (46, 4)):
            plant_tree(d, x, z)
    if L >= 3:
        lec = bldg(d, 12, 38, 38, 46, 1, "gable", "x", wh=5)
        ext_door(d, 25, Y0, 38, "north", double=True)
        lecture(d, (13, 39, 37, 45), Y0, "w", h=5)
        shelf_wall(d, (13, 39, 37, 45), "e", Y0, 3)
        chimney(d, 12, 42, Y0, lec["ridge"] + 1)
        lawn(d, 6, 16, 46, 36, "grass_block[snowy=false]")
        for x in range(6, 47):
            for z in range(16, 37):
                if (x * 7 + z * 3) % 11 == 0:
                    d.set(x, 1, z, "moss_block")
        path(d, 24, 15, 26, 37, "spruce_planks", border=False)
        cx, cz = 15, 26
        d.set(cx, 1, cz, "cobblestone")
        d.set(cx, Y0, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        for x in range(cx - 1, cx + 2):
            for z in range(cz - 1, cz + 2):
                if (x, z) != (cx, cz):
                    d.set(x, 1, z, "gravel")
        for (x, z, ax) in ((cx - 3, cz, "z"), (cx + 3, cz, "z"), (cx, cz - 3, "x"), (cx, cz + 3, "x"),
                           (cx - 3, cz - 1, "z"), (cx + 3, cz + 1, "z")):
            d.set(x, Y0, z, log("stripped_spruce_log", ax))
        for x, z in ((cx - 2, cz - 2), (cx + 2, cz - 2), (cx - 2, cz + 2), (cx + 2, cz + 2), (32, 22), (36, 28),
                     (25, 20), (25, 32)):
            d.spot(x, Y0, z, "leisure")
            keep(d, x, Y0, z)
        for x, z in ((34, 18), (42, 24), (30, 33), (9, 33), (20, 18)):
            plant_tree(d, x, z)
    if L >= 4:
        rl = bldg(d, 6, 17, 13, 34, 2, "gable", "z")
        ext_door(d, 13, Y0, 25, "west")
        r1 = (7, 18, 12, 33)
        stair_up(d, 12, 33, Y0, 7, "north") if False else stair_up(d, 8, 22, Y0, 7, "south")
        shelf_wall(d, r1, "w", Y0, 3)
        for z in range(19, 33, 4):
            desk(d, 11, Y0, z, "west")
        shelf_wall(d, r1, "w", 7, 2)
        shelf_wall(d, r1, "e", 7, 1)
        lights(d, r1, Y0)
        rug_in(d, r1, Y0, ("green_carpet",), pattern="plain")
        table_set(d, (8, 19, 11, 32), 7, "dining")
    if L >= 4:
        bk_nf = 2 if L >= 5 else 1
        bk = bldg(d, 38, 17, 46, 34, bk_nf, "gable", "z")
        ext_door(d, 38, Y0, 25, "east")
        if bk_nf > 1:
            stair_up(d, 45, 19, Y0, 7, "south")
            dorm(d, (39, 18, 45, 33), 7, 7, head="e")
        dorm(d, (39, 18, 45, 33), Y0, 7, head="e")
        chimney(d, 46, 30, Y0, bk["ridge"] + 1)
    if L >= 5:
        # mess hall lodge on the street, east of the chemistry cabin
        mh = bldg(d, 44, 4, 52, 15, 1, "gable", "z")
        ext_door(d, 48, Y0, 4, "south")
        kitchen(d, (45, 5, 51, 8), Y0)
        table_set(d, (45, 9, 51, 14), Y0, "dining")
        chimney(d, 52, 12, Y0, mh["ridge"] + 1)
        # fire-lookout tower at the quad corner
        tx1, tz1 = 31, 30
        for x, z in ((tx1, tz1), (tx1 + 4, tz1), (tx1, tz1 + 4), (tx1 + 4, tz1 + 4)):
            for y in range(Y0, 16):
                d.set(x, y, z, log("spruce_log"))
        for y in (7, 12):
            for a in range(1, 4):
                for (x, z, ax) in ((tx1 + a, tz1, "x"), (tx1 + a, tz1 + 4, "x"), (tx1, tz1 + a, "z"), (tx1 + 4, tz1 + a, "z")):
                    d.set(x, y, z, log("spruce_log", ax))
        d.fill(tx1, 15, tz1, tx1 + 4, 15, tz1 + 4, "spruce_planks")
        for x in range(tx1, tx1 + 5):
            for z in range(tz1, tz1 + 5):
                if x in (tx1, tx1 + 4) or z in (tz1, tz1 + 4):
                    d.set(x, 16, z, "spruce_fence")
        d.hip(tx1, tz1, tx1 + 4, tz1 + 4, 19, "dark_oak_stairs", "dark_oak_slab", overhang=1)
        for x, z in ((tx1, tz1), (tx1 + 4, tz1), (tx1, tz1 + 4), (tx1 + 4, tz1 + 4)):
            for y in range(16, 19):
                d.set(x, y, z, log("spruce_log"))
        d.set(tx1 + 2, 19, tz1 + 2, "spruce_planks")
        bell(d, tx1 + 2, 18, tz1 + 2)
        # faculty lodge (two storeys) in the south-east corner
        fl = bldg(d, 40, 39, 52, 51, 2, "gable", "x")
        ext_door(d, 48, Y0, 39, "south")
        stair_up(d, 42, 50, Y0, 7, "east")
        office(d, (41, 40, 45, 45), Y0)
        office(d, (47, 40, 51, 45), Y0, desk_side="s")
        lounge(d, (41, 46, 51, 50), Y0) if False else table_set(d, (46, 46, 51, 50), Y0, "dining")
        d.fill(46, Y0, 40, 46, 5, 45, "spruce_planks")
        arch(d, 46, Y0, 42, "east")
        dorm(d, (41, 40, 51, 50), 7, 8, head="n")
        chimney(d, 52, 45, Y0, fl["ridge"] + 1)
        # covered boardwalk round the quad (posts, rail, slab roof)
        for x in range(14, 38):
            for z in (15, 37):
                d.set(x, 1, z, "spruce_planks")
                d.set(x, 6, z, slab("spruce_slab"))
                if x % 4 == 2:
                    for y in range(Y0, 6):
                        d.set(x, y, z, log("spruce_log"))
                    d.set(x, 5, z + (1 if z == 15 else -1), "lantern[hanging=false,waterlogged=false]") if False else None
        for z in range(15, 38):
            for x in (14, 37):
                d.set(x, 1, z, "spruce_planks")
                d.set(x, 6, z, slab("spruce_slab"))
                if z % 4 == 3:
                    for y in range(Y0, 6):
                        d.set(x, y, z, log("spruce_log"))
        for x in range(16, 37, 4):
            d.set(x, 5, 15, "lantern[hanging=true,waterlogged=false]")
            d.set(x, 5, 37, "lantern[hanging=true,waterlogged=false]")
    return d


@design("university")
def university_v2(pack, rel, L):
    return common_materials({"Hearthwood": uni_hearthwood, "Cascadia": uni_cascadia, "Neoterra": uni_neoterra}[pack](rel, L))


def line_items(d, x, z, along, y, face, items, step=1):
    """Required work blocks in a row starting at (x,z) along +x ('x') or +z ('z'); the cell in front (direction
    `face`) is kept free. None leaves a gap. Returns next free position."""
    dx, dz = (1, 0) if along == "x" else (0, 1)
    fx, fz = D4[face]
    for i, it in enumerate(items):
        cx, cz = x + dx * i * step, z + dz * i * step
        if it is None:
            continue
        if it == "water_cauldron":
            d.item(cx, y, cz, "water_cauldron[level=3]")
        elif it == "rack":
            d.rack(cx, y, cz, face)
        else:
            d.item(cx, y, cz, it, face if it not in ("barrel",) else "up")
        keep(d, cx + fx, y, cz + fz)
        keep(d, cx, y, cz, 1)
    return x + dx * len(items) * step, z + dz * len(items) * step


def barrels(d, x, z, along, y, n, face, h=2):
    """Barrel shelving n cells long, h high (required barrels), aisle kept in front."""
    dx, dz = (1, 0) if along == "x" else (0, 1)
    fx, fz = D4[face]
    k = 0
    for i in range(n):
        cx, cz = x + dx * i, z + dz * i
        for j in range(h):
            d.item(cx, y + j, cz, "barrel", face)
            k += 1
        keep(d, cx + fx, y, cz + fz)
    return k


def work_items(d, L):
    """The town hall's work blocks for this level (barrels handled separately)."""
    out = []
    for k, n in sorted(d.req["items"].items()):
        k = k.split(":")[1]
        if k in ("barrel", "enchanting_table", "lectern", "ender_chest", "jukebox"):
            continue
        out += [k] * n
    return out


def market_stall(d, x, z, color, goods=("melon", "pumpkin[]", "hay_block[axis=y]")):
    """Market stall: counter, posts, striped wool awning, goods."""
    wood = d.S["wood"] if d.pack != "Neoterra" else "birch"
    for dx in (0, 2):
        for y in (2, 3, 4):
            put(d, x + dx, y, z, f"{wood}_fence")
            put(d, x + dx, y, z + 2, f"{wood}_fence")
    for dx in range(3):
        for dz in range(3):
            put(d, x + dx, 5, z + dz, f"{color if (dx % 2 == 0) else 'white'}_wool" if d.pack != "Neoterra" else
                f"{color}_concrete" if dx % 2 == 0 else "white_concrete")
    put(d, x + 1, 2, z, slab(f"{wood}_slab", "top"))
    put(d, x + 1, 3, z, ("melon", "pumpkin", "hay_block[axis=y]", "red_mushroom_block[down=true,east=true,north=true,south=true,up=true,west=true]")[(x + z) % 4])
    put(d, x + 1, 2, z + 2, "barrel[facing=up,open=false]") if False else put(d, x + 1, 2, z + 2, "composter[level=8]")


# ============================================================================================ TOWN HALL v2
def th_hearthwood(rel, L):
    d = new("Hearthwood", rel, (55, 36, 53))
    two = L >= 3
    nf = 2 if two else 1
    # ---- core guildhall (L1+): public hall
    c = bldg(d, 20, 14, 32, 22, nf, "gable", "x", win="nesw")
    d.hut(21, Y0, 15)
    keep(d, 22, Y0, 15)
    d.set(23, Y0, 15, slab("dark_oak_slab", "top"))
    put(d, 23, Y0 + 1, 15, "candle[candles=2,lit=false,waterlogged=false]")
    d.chair(23, Y0, 16, "south", "dark_oak", sit=False)
    long_table(d, 25, 18, 27, Y0, "dark_oak")
    line_items(d, 21, 17, "z", Y0, "east", ["crafting_table", "furnace", "furnace"])
    barrels(d, 31, 15, "z", Y0, 2, "west")
    d.bed(31, Y0, 21, "east")
    put(d, 31, Y0, 20, slab("dark_oak_slab", "top"))
    put(d, 31, Y0 + 1, 20, "candle[candles=1,lit=false,waterlogged=false]")
    rug_in(d, (21, 15, 31, 21), Y0, ("red_carpet", "yellow_carpet"))
    wall_art(d, (21, 15, 31, 21), Y0, "s", ("red", "yellow"))
    # entrance tower over the door (stub L1-2, clock & belfry L3+)
    tt = {1: 9, 2: 14}.get(L, 25)
    t = bldg(d, 24, 9, 28, 14, 1, "flat", wh=tt - 1, mat="stone_bricks", up="stone_bricks", win="", deco=False,
             parapet=False)
    d.clear(25, Y0, 14, 27, 4, 14)
    ext_door(d, 26, Y0, 9, "south")
    d.sign(26, 5, 8, "north", ["TOWN", "HALL"], "dark_oak")
    d.banner(25, 6, 8, "north", "red")
    d.banner(27, 6, 8, "north", "red")
    d.fill(25, 6, 10, 27, 6, 13, "dark_oak_planks")
    by = tt - 3
    d.fill(25, by, 10, 27, by, 13, "dark_oak_planks")
    for y in range(by + 1, tt):
        for x in range(25, 28):
            d.set(x, y, 9, AIR)
            d.set(x, y, 14, AIR)
        for z in range(10, 14):
            d.set(24, y, z, AIR)
            d.set(28, y, z, AIR)
    bell(d, 26, tt - 1, 11)
    d.fill(24, tt, 9, 28, tt, 14, "stone_bricks")
    rt = d.hip(24, 9, 28, 14, tt + 1, f"{d.S['roof']}_stairs", f"{d.S['roof']}_slab", overhang=1)
    d.set(26, rt + 1, 11, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    if two:
        clockface(d, 26, by - 3, 9, "north", "white_concrete")
        clockface(d, 24, by - 3, 11, "west", "white_concrete")
        clockface(d, 28, by - 3, 11, "east", "white_concrete")
        for x in range(24, 29):
            put(d, x, by - 6, 8, st("stone_brick_stairs", "south", "top"))
    # forecourt: patterned paving, lamp posts, flower beds
    for x in range(14, 39):
        for z in range(1, 9):
            d.set(x, 1, z, "stone_bricks" if (x + z) % 3 else "polished_andesite")
    for x in (21, 31):
        post_lamp(d, x, 7)
    flowerbed(d, 20, 12, 23, 13)
    flowerbed(d, 29, 12, 32, 13)
    # ---- L2: workshop wing (west) + stores wing (east)
    if L >= 2:
        w = bldg(d, 8, 14, 20, 22, nf, "gable", "x", mat="bricks", up="calcite")
        link(d, 20, Y0, 18, "west")
        items = work_items(d, L)
        a, b = items[:11], items[11:]
        line_items(d, 9, 15, "x", Y0, "south", a[:11])
        line_items(d, 9, 21, "x", Y0, "north", b + [None] * 0)
        d.hearth(13, Y0, 18, "north", 6, "bricks", "campfire") if False else None
        for x in range(11, 18):
            if x % 2:
                put(d, x, Y0, 18, slab("dark_oak_slab", "top"))
                put(d, x, Y0 + 1, 18, ("flower_pot", "candle[candles=2,lit=false,waterlogged=false]")[x % 4 == 1])
        lights(d, (9, 15, 19, 21), Y0)
        chimney(d, 8, 16, Y0, w["ridge"] + 1)
        d.sign(14, 5, 13, "north", ["Guild", "Workshop"], "dark_oak")
        ext_door(d, 8, Y0, 18, "east")
        s_ = bldg(d, 32, 14, 44, 22, nf, "gable", "x", mat="bricks", up="calcite")
        link(d, 32, Y0, 18, "east")
        nb = need(d, "barrel") - 4
        barrels(d, 33, 15, "x", Y0, min(11, (nb + 1) // 2), "south")
        if nb > 22:
            pass
        rest = nb - 2 * min(11, (nb + 1) // 2)
        if rest > 0:
            barrels(d, 33, 21, "x", Y0, (rest + 1) // 2, "north")
        ext_door(d, 44, Y0, 18, "west", double=True, along="z")
        store(d, (33, 17, 43, 20), Y0)
        cart(d, 47, 16, "z")
        put(d, 47, 2, 21, "hay_block[axis=y]")
        path(d, 45, 18, 52, 19, border=False)
    # ---- L3: upper floor: archive (W), council chamber (centre), quarters (E)
    if two:
        stair_up(d, 22, 21, Y0, 7, "east")
        link(d, 20, 7, 18, "east")
        link(d, 32, 7, 18, "east")
        for x in range(23, 30):
            pass
        long_table(d, 24, 17, 29, 7, "dark_oak", top="dark_oak_planks")
        d.item(30, 7, 15, "lectern", "west")
        keep(d, 29, 7, 15)
        if L >= 4:
            d.item(21, 7, 15, "jukebox")
            keep(d, 22, 7, 15)
        wall_art(d, (21, 15, 31, 21), 7, "n", ("red", "yellow"))
        rug_in(d, (21, 15, 31, 20), 7, ("red_carpet",), inset=1, pattern="plain")
        shelf_wall(d, (9, 15, 19, 21), "n", 7, 3)
        shelf_wall(d, (9, 15, 19, 21), "w", 7, 3)
        d.item(14, 7, 19, "enchanting_table")
        keep(d, 14, 7, 20)
        for z in (17, 20):                                          # freestanding record presses
            stall_row(d, 11, 12, z, 7, 2)
        for z in (17, 20):                                          # clerks' desks under the windows
            desk(d, 18, 7, z, "west", sit=False)
        d.rug(13, 18, 15, 20, 7, ("green_carpet",), "plain")
        lights(d, (9, 15, 19, 21), 7)
        dorm(d, (33, 15, 43, 21), 7, 5, head="n")
        if L >= 4:
            d.item(43, 7, 21, "ender_chest", "west")
            keep(d, 42, 7, 21)
    # ---- L4: rear wing – banquet hall & kitchen below, mayor's apartment above
    if L >= 4:
        r = bldg(d, 20, 22, 32, 35, 2, "gable", "z", mat="bricks", up="calcite")
        link(d, 26, Y0, 22, "south")
        long_table_z(d, 26, 25, 31, Y0, "dark_oak")
        kitchen(d, (21, 31, 31, 34), Y0)
        wall_art(d, (21, 23, 31, 33), Y0, "ew", ("red", "yellow"))
        stair_up(d, 31, 24, Y0, 7, "south")
        office(d, (21, 23, 30, 27), 7)
        dorm(d, (21, 29, 31, 34), 7, 2, head="s")
        lounge(d, (21, 28, 31, 34), 7)
        chimney(d, 32, 30, Y0, r["ridge"] + 1)
        # walled garden behind with a bandstand
        lawn(d, 8, 36, 46, 51)
        for x in range(8, 47):
            put(d, x, 2, 51, "brick_wall")
        for z in range(36, 52):
            put(d, 8, 2, z, "brick_wall")
            put(d, 46, 2, z, "brick_wall")
        path(d, 25, 35, 27, 50)
        bx, bz = 26, 43
        for x in range(bx - 3, bx + 4):
            for z in range(bz - 3, bz + 4):
                if abs(x - bx) + abs(z - bz) <= 4:
                    d.set(x, 1, z, "stone_bricks")
        for x, z in ((bx - 2, bz - 2), (bx + 2, bz - 2), (bx - 2, bz + 2), (bx + 2, bz + 2)):
            for y in range(Y0, 6):
                d.set(x, y, z, "dark_oak_fence")
        d.hip(bx - 2, bz - 2, bx + 2, bz + 2, 6, "deepslate_tile_stairs", "deepslate_tile_slab", overhang=1)
        for x, z in ((12, 40), (40, 40), (12, 48), (40, 48)):
            plant_tree(d, x, z)
        flowerbed(d, 15, 37, 22, 38)
        flowerbed(d, 30, 37, 37, 38)
        flowerbed(d, 10, 49, 22, 50)
        flowerbed(d, 30, 49, 44, 50)
        for x, z in ((21, 42), (31, 42), (21, 46), (31, 46)):
            post_lamp(d, x, z)
        for x, z in ((18, 44), (33, 44)):
            park_bench(d, x, z, "x", "south")
    # ---- L5: market square with stalls & fountain; courthouse (W) and guard house (E) round the garden
    if L >= 5:
        fountain(d, 26, 4, 2)
        for x, col in ((15, "red"), (35, "blue")):
            market_stall(d, x, 2, col)
        for x, col in ((10, "yellow"), (40, "green")):
            market_stall(d, x, 5, col)
        ch = bldg(d, 8, 24, 18, 34, 2, "gable", "z", mat="stone_bricks", up="stone_bricks", gable_end="stone_bricks")
        ext_door(d, 13, Y0, 24, "south")
        for x in range(9, 18):
            pass
        d.item(13, Y0, 32, "lectern", "north") if False else put(d, 13, Y0, 32, "dark_oak_planks")
        lecture(d, (9, 25, 17, 33), Y0, "s")
        stair_up(d, 9, 26, Y0, 7, "south")
        office(d, (9, 25, 17, 33), 7)
        shelf_wall(d, (9, 25, 17, 33), "e", 7, 3)
        d.sign(13, 5, 23, "north", ["COURT", "HOUSE"], "dark_oak")
        gh = bldg(d, 34, 24, 44, 34, 2, "gable", "z", mat="bricks", up="calcite")
        ext_door(d, 39, Y0, 24, "south")
        d.sign(39, 5, 23, "north", ["WATCH", "HOUSE"], "dark_oak")
        table_set(d, (35, 25, 43, 29), Y0, "dining")
        for x in range(36, 43, 2):                                 # cells
            d.fill(x, Y0, 31, x, 4, 33, "iron_bars")
        stair_up(d, 43, 27, Y0, 7, "south")
        dorm(d, (35, 25, 42, 33), 7, 6, head="w")
        # covered market house: open arcade below, corn exchange above
        mx1, mz1, mx2, mz2 = 46, 24, 54, 36
        m = bldg(d, mx1, mz1, mx2, mz2, 2, "gable", "z", mat="stone_bricks", up="calcite")
        for x in range(mx1, mx2 + 1):
            for z in range(mz1, mz2 + 1):
                if (x in (mx1, mx2) or z in (mz1, mz2)) and not ((x in (mx1, mx2) and (z - mz1) % 3 == 0) or
                                                                 (z in (mz1, mz2) and (x - mx1) % 4 == 0)):
                    for y in range(Y0, 6):
                        d.set(x, y, z, AIR)
                    d.set(x, 5, z, "stone_brick_slab[type=top,waterlogged=false]")
        for x, z, col in ((48, 27, "red"), (51, 27, "yellow"), (48, 31, "green"), (51, 31, "blue")):
            put(d, x, Y0, z, slab("dark_oak_slab", "top"))
            put(d, x + 1, Y0, z, f"{col}_wool")
            put(d, x, Y0 + 1, z, ("melon", "pumpkin", "hay_block[axis=y]", "carved_pumpkin[facing=north]")[x % 4])
        stair_up(d, 47, 35, Y0, 7, "north") if False else stair_up(d, 53, 34, Y0, 7, "north")
        table_set(d, (47, 25, 52, 35), 7, "dining")
        d.sign(50, 6, 23, "north", ["MARKET", "HOUSE"], "dark_oak")
        for z in (26, 30):
            put(d, 33, 4, z, "lantern[hanging=false,waterlogged=false]") if False else None
    return d


def th_neoterra(rel, L):
    d = new("Neoterra", rel, (53, 45, 49), paving="smooth_stone")
    Q = "smooth_quartz"
    two = L >= 3
    nf = 2 if two else 1
    c = bldg(d, 18, 12, 32, 22, nf, "flat", glassy=True, win="nesw")
    ext_door(d, 24, Y0, 12, "south", double=True)
    d.hut(19, Y0, 13)
    keep(d, 20, Y0, 13)
    for x in range(21, 24):
        d.set(x, Y0, 15, Q)
    d.chair(22, Y0, 16, "south", "mangrove", sit=False)
    for x, z in ((25, 17), (26, 17), (25, 18), (26, 18)):
        d.table(x, Y0, z, "birch", "block", Q)
    for x in (25, 26):
        d.chair(x, Y0, 16, "north", "birch")
        d.chair(x, Y0, 19, "south", "birch")
    for z in (17, 18):
        d.chair(24, Y0, z, "west", "birch")
        d.chair(27, Y0, z, "east", "birch")
    line_items(d, 19, 17, "z", Y0, "east", ["crafting_table", "furnace", "furnace"])
    barrels(d, 31, 13, "z", Y0, 2, "west")
    d.bed(31, Y0, 21, "east", "cyan")
    put(d, 31, Y0, 20, "white_concrete")
    put(d, 31, Y0 + 1, 20, "end_rod[facing=up]")
    corners(d, (19, 13, 31, 21), Y0, ["potted_bamboo"])
    for x in range(20, 31):
        for z in (12, 11, 10, 9):
            pass
    for x in range(21, 30):                                         # entrance canopy
        for z in range(8, 12):
            put(d, x, 6 if not two else 6, z, slab("smooth_quartz_slab", "top"))
    d.sign(25, 7 if two else 7, 11, "north", ["CIVIC", "CENTRE"], "birch", glow=True, color="cyan") if False else \
        d.sign(25, 6 if not two else 7, 11 if two else 7, "north", ["CIVIC", "CENTRE"], "birch", glow=True, color="cyan")
    # plaza paving pattern
    for x in range(10, 41):
        for z in range(1, 12):
            if d.get(x, 1, z) == "minecraft:smooth_stone":
                d.set(x, 1, z, "polished_diorite" if (x // 2 + z // 2) % 2 else "smooth_stone")
    for x in (20, 30):
        post_lamp(d, x, 4)
    for x in (16, 34):
        put(d, x, 2, 9, "moss_block")
        put(d, x, 3, 9, "flowering_azalea")
    if L >= 2:
        w = bldg(d, 6, 12, 18, 22, nf, "flat", glassy=True, win="nsw")
        link(d, 18, Y0, 17, "west")
        items = work_items(d, L)
        line_items(d, 7, 13, "x", Y0, "south", items[:11])
        line_items(d, 7, 21, "x", Y0, "north", items[11:])
        for x in range(9, 16):
            put(d, x, Y0, 17, slab("smooth_quartz_slab", "top"))
            put(d, x, Y0 + 1, 17, ("flower_pot", "end_rod[facing=up]", AIR)[x % 3]) if x % 3 < 2 else None
        ext_door(d, 6, Y0, 17, "east")
        d.sign(12, 6, 11, "north", ["MAKER", "SPACE"], "birch", glow=True, color="orange")
        s_ = bldg(d, 32, 12, 44, 22, nf, "flat", glassy=False, win="ns")
        link(d, 32, Y0, 17, "east")
        nb = need(d, "barrel") - 4
        barrels(d, 33, 13, "x", Y0, min(11, (nb + 1) // 2), "south")
        rest = nb - 2 * min(11, (nb + 1) // 2)
        if rest > 0:
            barrels(d, 33, 21, "x", Y0, (rest + 1) // 2, "north")
        ext_door(d, 44, Y0, 17, "west", double=True, along="z")
        store(d, (33, 15, 43, 19), Y0)
        # clock fin with bell frame
        ft = 17 if L == 2 else 28
        for x in range(46, 49):
            for z in range(7, 10):
                for y in range(Y0, ft + 1):
                    d.set(x, y, z, "white_concrete")
        for y in range(Y0 + 1, ft - 3):
            d.set(47, y, 7, "cyan_stained_glass")
        clockface(d, 47, ft - 1, 7, "north", "black_concrete", hand="sea_lantern")
        for x, z in ((46, 7), (48, 7), (46, 9), (48, 9)):
            for y in range(ft + 1, ft + 4):
                d.set(x, y, z, "quartz_pillar[axis=y]")
        d.fill(46, ft + 4, 7, 48, ft + 4, 9, Q)
        bell(d, 47, ft + 3, 8)
        d.set(47, ft + 5, 8, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    if two:
        stair_up(d, 20, 21, Y0, 7, "east")
        link(d, 18, 7, 17, "east")
        link(d, 32, 7, 17, "east")
        for x in range(22, 29):                                     # horseshoe council table
            d.table(x, 7, 19, "birch", "block", Q)
            d.chair(x, 7, 20, "south", "mangrove")
        for z in (15, 16, 17, 18):
            for x, back in ((22, "west"), (28, "east")):
                d.table(x, 7, z, "birch", "block", Q)
                d.chair(x + (-1 if back == "west" else 1), 7, z, back, "mangrove")
        d.item(25, 7, 13, "lectern", "south")
        keep(d, 25, 7, 14)
        d.banner(25, 9, 13, "south", "cyan") if False else None
        if L >= 4:
            d.item(30, 7, 13, "jukebox")
            keep(d, 30, 7, 14)
        shelf_wall(d, (7, 13, 17, 21), "w", 7, 3)
        shelf_wall(d, (7, 13, 17, 21), "s", 7, 3)
        d.item(12, 7, 16, "enchanting_table")
        keep(d, 12, 7, 17)
        table_set(d, (8, 13, 16, 15), 7, "study", sit=False)
        dorm(d, (33, 13, 43, 21), 7, 5, head="n")
        if L >= 4:
            d.item(43, 7, 21, "ender_chest", "west")
            keep(d, 42, 7, 21)
        for b in (w, s_):
            roof_garden(d, b, "garden" if b is w else "solar")
    if L >= 4:
        r = bldg(d, 18, 22, 32, 34, 3, "flat", glassy=True, win="esw")
        link(d, 25, Y0, 22, "south")
        long_table(d, 21, 27, 29, Y0, "birch", top=Q)
        long_table(d, 21, 30, 29, Y0, "birch", top=Q)
        kitchen(d, (19, 33, 31, 33), Y0) if False else None
        corners(d, (19, 23, 31, 33), Y0, ["potted_bamboo"])
        stair_up(d, 31, 24, Y0, 7, "south")
        office(d, (19, 23, 25, 33), 7)
        lounge(d, (26, 23, 30, 33), 7)
        stair_up(d, 19, 32, 7, 12, "north")
        table_set(d, (20, 23, 31, 33), 12, "study", sit=False)
        roof_garden(d, r, "garden")
        fountain(d, 25, 4, 2)
        for x, z in ((12, 3), (38, 3), (12, 8), (38, 8)):
            plant_tree(d, x, z)
        for x in (15, 33):
            park_bench(d, x, 5, "x", "north")
    if L >= 5:
        tw = bldg(d, 34, 24, 46, 40, 6, "flat", glassy=True, win="nsew")
        ext_door(d, 40, Y0, 40, "north", double=True)
        link(d, 34, Y0, 30, "east") if False else None
        for k in range(5):
            stair_up(d, 35 if k % 2 == 0 else 45, 25 if k % 2 == 0 else 39, Y0 + 5 * k, Y0 + 5 * k + 5,
                     "south" if k % 2 == 0 else "north")
        lounge(d, (36, 26, 44, 38), Y0)
        for k in range(1, 6):
            y = Y0 + 5 * k
            office(d, (36, 25, 44, 31), y)
            table_set(d, (36, 33, 44, 38), y, "study", sit=False)
        roof_garden(d, tw, "solar")
        for i, b in enumerate((c,)):
            roof_garden(d, b, "garden")
        for x, col in ((8, "orange"), (42, "lime")):
            market_stall(d, x, 4, col)
        d.sign(40, 6, 41, "south", ["CITY", "OFFICES"], "birch", glow=True, color="cyan")
    return d


def th_cascadia(rel, L):
    d = new("Cascadia", rel, (55, 34, 55), paving="coarse_dirt")
    loft = L >= 3
    c = bldg(d, 14, 10, 28, 22, 2 if loft else 1, "gable", "z")
    ext_door(d, 21, Y0, 10, "south")
    d.fill(13, 1, 5, 29, 1, 9, "spruce_planks")                   # porch
    for x in (13, 17, 25, 29):
        for y in range(Y0, 6):
            put(d, x, y, 5, log("spruce_log"))
    for x in range(12, 31):
        d.set(x, 6, 4, st("spruce_stairs", "south"))
        for z in range(5, 10):
            d.set(x, 6, z, slab("spruce_slab"))
    for x in range(14, 29):
        if x not in (13, 17, 25, 29) and abs(x - 21) > 1:
            put(d, x, Y0, 5, "spruce_fence")
    d.sign(21, 5, 9, "north", ["GRANGE", "HALL"], "spruce")
    for x in (15, 27):
        d.chair(x, Y0, 7, "south", "spruce", sit=False)
    d.hut(15, Y0, 11)
    keep(d, 16, Y0, 11)
    for z in range(13, 18):
        d.table(21, Y0, z, "spruce", "block", "stripped_spruce_wood[axis=y]")
        d.chair(20, Y0, z, "west", "spruce")
        d.chair(22, Y0, z, "east", "spruce")
    d.chair(21, Y0, 18, "south", "spruce")
    line_items(d, 27, 11, "z", Y0, "west", ["crafting_table", "furnace", "furnace"])
    barrels(d, 27, 15, "z", Y0, 2, "west")
    d.bed(15, Y0, 19, "west")
    put(d, 15, Y0, 20, slab("spruce_slab", "top"))
    d.hearth(15, Y0, 16, "east", c["ridge"] + 2, "cobblestone", "campfire")
    chimney(d, 13, 16, Y0, c["ridge"] + 1)
    rug_in(d, (16, 12, 26, 20), Y0, ("brown_carpet", "green_carpet"))
    if L >= 2:
        w = bldg(d, 14, 22, 28, 32, 1, "gable", "z")
        link(d, 21, Y0, 22, "south")
        items = work_items(d, L)
        line_items(d, 15, 23, "z", Y0, "east", items[:9])
        line_items(d, 27, 23, "z", Y0, "west", items[9:])
        workshop(d, (17, 24, 25, 31), Y0)
        ext_door(d, 21, Y0, 32, "north", double=True)
        chimney(d, 28, 27, Y0, w["ridge"] + 1)
        # barrel shed lean-to
        nb = need(d, "barrel") - 4
        sh = bldg(d, 29, 12, 35, 22, 1, "gable", "z", win="e")
        link(d, 29, Y0 if False else Y0, 19, "east") if False else None
        ext_door(d, 32, Y0, 12, "south", double=False)
        barrels(d, 34, 13, "z", Y0, min(9, (nb + 1) // 2), "west")
        rest = nb - 2 * min(9, (nb + 1) // 2)
        if rest > 0:
            barrels(d, 30, 14, "z", Y0, (rest + 1) // 2, "east")
        for x, z in ((38, 14), (39, 14)):
            for y in (2, 3):
                put(d, x, y, z, log("spruce_log", "z"))
        cart(d, 37, 18, "z")
    if loft:
        stair_up(d, 17, 21, Y0, 7, "east")
        shelf_wall(d, (16, 11, 26, 15), "w", 7, 3)
        shelf_wall(d, (16, 11, 26, 15), "n", 7, 3)
        shelf_wall(d, (16, 11, 26, 15), "e", 7, 2)
        d.item(21, 7, 13, "enchanting_table")
        d.item(18, 7, 16, "lectern", "south")
        keep(d, 18, 7, 17)
        keep(d, 21, 7, 14)
        if L >= 4:
            d.item(15, 7, 19, "ender_chest", "east")
            keep(d, 16, 7, 19)
        dorm(d, (15, 17, 25, 21), 7, 5, head="n")
        # fire-lookout bell tower
        tx1, tz1 = 40, 4
        for x, z in ((tx1, tz1), (tx1 + 4, tz1), (tx1, tz1 + 4), (tx1 + 4, tz1 + 4)):
            for y in range(Y0, 18):
                d.set(x, y, z, log("spruce_log"))
        for y in (7, 12):
            for a in range(1, 4):
                for (x, z, ax) in ((tx1 + a, tz1, "x"), (tx1 + a, tz1 + 4, "x"), (tx1, tz1 + a, "z"),
                                   (tx1 + 4, tz1 + a, "z")):
                    d.set(x, y, z, log("spruce_log", ax))
        d.fill(tx1, 17, tz1, tx1 + 4, 17, tz1 + 4, "spruce_planks")
        for x in range(tx1, tx1 + 5):
            for z in range(tz1, tz1 + 5):
                if x in (tx1, tx1 + 4) or z in (tz1, tz1 + 4):
                    d.set(x, 18, z, "spruce_fence")
        for x, z in ((tx1, tz1), (tx1 + 4, tz1), (tx1, tz1 + 4), (tx1 + 4, tz1 + 4)):
            for y in range(18, 21):
                d.set(x, y, z, log("spruce_log"))
        d.hip(tx1, tz1, tx1 + 4, tz1 + 4, 21, "dark_oak_stairs", "dark_oak_slab", overhang=1)
        d.set(tx1 + 2, 21, tz1 + 2, "spruce_planks")
        bell(d, tx1 + 2, 20, tz1 + 2)
    else:
        for y in range(Y0, 6):
            d.set(32, y, 6, log("spruce_log"))
            d.set(34, y, 6, log("spruce_log"))
        d.fill(32, 6, 6, 34, 6, 6, log("spruce_log", "x"))
        bell(d, 33, 5, 6)
    if L >= 4:
        m = bldg(d, 2, 10, 12, 24, 2, "gable", "z")
        ext_door(d, 7, Y0, 10, "south")
        d.sign(7, 5, 9, "north", ["MAYOR"], "spruce")
        stair_up(d, 11, 12, Y0, 7, "south")
        lounge(d, (3, 11, 10, 16), Y0)
        kitchen(d, (3, 17, 10, 21), Y0)
        table_set(d, (4, 17, 9, 21), Y0, "dining")
        office(d, (3, 11, 11, 16), 7)
        d.item(3, 7, 21, "jukebox")
        keep(d, 4, 7, 21)
        for x in (3, 11):                                            # porch posts and roof over the mayor's door
            for y in range(Y0, 5):
                put(d, x, y, 9, log("spruce_log"))
        for x in range(2, 13):
            for z in (8, 9):
                put(d, x, 5, z, slab("spruce_slab"))
        dorm(d, (3, 17, 11, 21), 7, 2, head="w")
        chimney(d, 2, 16, Y0, m["ridge"] + 1)
        for x in range(1, 13):
            put(d, x, 2, 6, "spruce_fence")
        flowerbed(d, 2, 7, 5, 8, ("fern", "blue_orchid", "allium", "lily_of_the_valley"))
        flowerbed(d, 9, 7, 12, 8, ("fern", "blue_orchid", "allium", "lily_of_the_valley"))
        plant_tree(d, 4, 3)
        plant_tree(d, 10, 3)
    if L >= 5:
        f = bldg(d, 36, 14, 48, 28, 2, "gable", "z", mat="mangrove_planks", up="mangrove_planks")
        d.double_door(41, Y0, 14, "x", "south", "spruce")
        for x in (40, 43):
            d.set(x, Y0, 14, AIR)
            d.set(x, Y0 + 1, 14, AIR)
            d.set(x, Y0 + 2, 14, AIR)
        d.sign(42, 6, 13, "north", ["FIRE", "HALL"], "spruce")
        for z in range(16, 26):                                      # engine bay: cart, hoses
            put(d, 42, Y0, z, "red_wool" if z % 3 else "barrel[facing=up,open=false]") if z in (18, 19, 20) else None
        cart(d, 41, 18, "z")
        kitchen(d, (37, 15, 40, 27), Y0)
        table_set(d, (37, 20, 40, 27), Y0, "dining")
        for z in range(16, 26, 2):
            put(d, 47, Y0 + 1, z, "lantern[hanging=false,waterlogged=false]") if False else None
        stair_up(d, 47, 22, Y0, 7, "south")
        dorm(d, (37, 15, 45, 26), 7, 6, head="w", desks=False)
        for y in range(Y0, 24):                                      # hose-drying tower
            for x, z in ((50, 22), (52, 22), (50, 24), (52, 24)):
                d.set(x, y, z, log("spruce_log"))
            if y % 5 == 0:
                for x in (50, 51, 52):
                    d.set(x, y, 22, log("spruce_log", "x"))
                    d.set(x, y, 24, log("spruce_log", "x"))
        d.hip(50, 22, 52, 24, 24, "dark_oak_stairs", "dark_oak_slab", overhang=1)
        jl = bldg(d, 36, 34, 46, 42, 1, "gable", "x", mat="cobblestone", up="cobblestone", gable_end="cobblestone")
        ext_door(d, 41, Y0, 34, "south")
        d.sign(41, 5, 33, "north", ["JAIL"], "spruce")
        for x in range(38, 45, 2):
            d.fill(x, Y0, 39, x, 4, 41, "iron_bars")
        table_set(d, (37, 35, 45, 37), Y0, "dining")
        lv = bldg(d, 2, 28, 12, 42, 1, "gable", "z", mat="stripped_spruce_log")
        ext_door(d, 7, Y0, 28, "south", double=True)
        for z in range(30, 42, 3):                                  # stalls with hay
            for x in (3, 11):
                put(d, x, Y0, z, "hay_block[axis=y]")
            d.fill(4, Y0, z + 2, 4, Y0 + 1, z + 2, "spruce_fence")
            d.fill(10, Y0, z + 2, 10, Y0 + 1, z + 2, "spruce_fence")
        d.sign(7, 5, 27, "north", ["LIVERY"], "spruce")
        # boardwalk main street with hitching rails and lamps
        for x in range(0, 55):
            for z in range(0, 3):
                d.set(x, 1, z, "spruce_planks")
        for x in range(2, 53, 6):
            put(d, x, 2, 3, "spruce_fence")
            put(d, x, 3, 3, "lantern[hanging=false,waterlogged=false]")
    return d


@design("townhall")
def townhall_v2(pack, rel, L):
    return common_materials({"Hearthwood": th_hearthwood, "Cascadia": th_cascadia, "Neoterra": th_neoterra}[pack](rel, L))




# ============================================================================================ HOSPITAL v2
def dispensary(d, x, z, along, y, face, L):
    """Brewing stand, furnace (steriliser), wash basin, supply rack (L2+), barrels (L3+) in a row."""
    items = ["brewing_stand", "furnace", "water_cauldron"]
    if d.req["racks"]:
        items.append("rack")
    items += ["barrel"] * need(d, "barrel")
    line_items(d, x, z, along, y, face, items)


def beds_left(d):
    return d.req["beds"] - d.placed["beds"]


def hosp_hearthwood(rel, L):
    d = new("Hearthwood", rel, (55, 30, 51))
    adm_nf = 2 if L >= 3 else 1
    a = bldg(d, 22, 8, 32, 18, adm_nf, "gable", "z")
    ext_door(d, 27, Y0, 8, "south")
    for x in (25, 29):                                              # porch
        for y in range(Y0, 5):
            put(d, x, y, 5, "oak_fence")
    d.fill(25, 5, 5, 29, 5, 7, "oak_planks")
    d.gable(25, 5, 29, 7, 6, "z", f"{d.S['roof']}_stairs", f"{d.S['roof']}_slab", "calcite", overhang=0)
    d.fill(25, 1, 4, 29, 1, 7, "stone_bricks")
    d.sign(27, 4, 4, "north", ["COTTAGE", "HOSPITAL"], "oak")
    d.hut(23, Y0, 9)
    keep(d, 24, Y0, 9)
    if d.req["seats"]:
        d.chair(29, Y0, 9, "north", "oak")
        d.chair(30, Y0, 9, "north", "oak")
    put(d, 31, Y0, 9, "potted_red_tulip")
    for x in (27, 28, 29):
        put(d, x, Y0, 12, slab("dark_oak_slab", "top"))
    d.chair(28, Y0, 13, "south", "oak", sit=False)
    put(d, 27, Y0 + 1, 12, "candle[candles=1,lit=false,waterlogged=false]")
    line_items(d, 31, 10, "z", Y0, "west", ["brewing_stand", "furnace", "water_cauldron"])
    if d.req["racks"]:
        line_items(d, 31, 16, "z", Y0, "west", ["rack"])
    line_items(d, 28, 17, "x", Y0, "north", ["barrel"] * need(d, "barrel"))
    chimney(d, 32, 12, Y0, a["ridge"] + 1)
    flowerbed(d, 22, 2, 24, 6)
    flowerbed(d, 30, 2, 32, 6)
    for x in (20, 34):
        post_lamp(d, x, 4)
    if L == 1:
        ward(d, (23, 14, 24, 17), Y0, beds_left(d), head=("w",))
    if L >= 2:
        e = bldg(d, 32, 10, 46, 18, 2 if L >= 4 else 1, "gable", "x", win="nse")
        link(d, 32, Y0, 14, "east")
        ward(d, (33, 11, 45, 17), Y0, min(beds_left(d), {2: 4, 3: 4}.get(L, 6)), head=("n", "s"))
        d.sign(39, 5, 9, "north", ["VICTORIA", "WARD"], "oak")
        chimney(d, 46, 14, Y0, e["ridge"] + 1)
    if L >= 3:
        stair_up(d, 25, 12, Y0, 7, "south")
        dorm(d, (26, 9, 31, 17), 7, 3, head="e", color="white")
        office(d, (23, 9, 24, 17), 7) if False else corners(d, (23, 9, 31, 17), 7)
        w = bldg(d, 8, 10, 22, 18, 2 if L >= 4 else 1, "gable", "x", win="nsw")
        link(d, 22, Y0, 14, "west")
        ward(d, (9, 11, 21, 17), Y0, min(beds_left(d), 2 if L == 3 else 4), head=("n", "s"))
        d.sign(15, 5, 9, "north", ["ALBERT", "WARD"], "oak")
        lawn(d, 8, 2, 20, 7)
        lawn(d, 32, 2, 44, 7)
        for x in (11, 17, 35, 41):
            plant_tree(d, x, 4)
    if L >= 4:
        stair_up(d, 34, 15, Y0, 7, "east")
        stair_up(d, 20, 15, Y0, 7, "west")
        ward(d, (33, 11, 45, 16), 7, beds_left(d), head=("n",))
        lounge(d, (9, 11, 21, 17), 7)
        # surgery wing behind the admin block
        s_ = bldg(d, 22, 18, 32, 30, 1, "gable", "z", wh=5)
        link(d, 26, Y0, 18, "south")
        cx, cz = 27, 24                                             # operating table under a lamp
        d.set(cx, Y0, cz, "white_concrete")
        d.set(cx, Y0, cz + 1, "white_concrete")
        put(d, cx, 6, cz, "chain[axis=y,waterlogged=false]") if False else None
        d.set(cx, 6, cz, "sea_lantern") if False else None
        line_items(d, 23, 29, "x", Y0, "north", [])
        for x in range(23, 32):
            if x % 2:
                put(d, x, Y0, 29, "water_cauldron[level=3]" if x % 4 == 1 else slab("smooth_stone_slab", "top"))
                put(d, x, Y0 + 1, 29, "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]") if x % 4 == 3 else None
        for z in (21, 27):
            put(d, 23, Y0, z, "white_wool")
            put(d, 31, Y0, z, "white_wool")
        lights(d, (23, 19, 31, 29), Y0, 5)
        d.sign(27, 5, 31, "south", ["OPERATING", "THEATRE"], "oak")
    if L >= 5:
        # children's / maternity wing behind the west ward + chapel + walled garden + carriage house
        m = bldg(d, 8, 18, 20, 30, 2, "gable", "z", mat="calcite", up="calcite")
        link(d, 14, Y0, 18, "south")
        ward(d, (9, 19, 19, 29), Y0, 6, head=("w", "e"), color="light_blue")
        for z in range(20, 29, 2):
            put(d, 14, Y0, z, "white_wool") if False else None
        stair_up(d, 19, 20, Y0, 7, "south")
        lounge(d, (9, 19, 19, 24), 7)
        table_set(d, (9, 25, 19, 29), 7, "study", sit=False)
        d.sign(14, 5, 31, "south", ["CHILDREN'S", "WARD"], "oak")
        ch = bldg(d, 36, 22, 44, 34, 1, "gable", "z", mat="stone_bricks", up="stone_bricks", gable_end="stone_bricks", wh=6)
        ext_door(d, 40, Y0, 22, "south")
        for z in range(25, 32, 2):
            for x in (38, 39, 41, 42):
                d.chair(x, Y0, z, "south", "oak", sit=False)
        d.set(40, Y0, 33, "oak_planks")
        put(d, 40, Y0 + 1, 33, "candle[candles=4,lit=false,waterlogged=false]")
        d.window(40, 4, 34, 40, 6, 34, "light_blue_stained_glass_pane")
        lights(d, (37, 23, 43, 33), Y0, 6)
        lawn(d, 1, 32, 54, 50)
        for x in range(1, 54):
            put(d, x, 2, 50, "brick_wall")
        for z in range(32, 51):
            put(d, 0, 2, z, "brick_wall")
            put(d, 54, 2, z, "brick_wall")
        path(d, 25, 31, 27, 49)
        path(d, 2, 40, 53, 41)
        for x, z in ((6, 36), (20, 36), (32, 46), (48, 36), (12, 46), (46, 46)):
            plant_tree(d, x, z)
        for x in range(4, 52, 6):
            flowerbed(d, x, 43, x + 2, 44)
        for x, z in ((15, 38), (36, 38)):
            park_bench(d, x, z, "x", "north")
        fountain(d, 26, 45, 2)
        cr = bldg(d, 47, 8, 54, 18, 1, "gable", "z", mat="bricks")
        d.double_door(50, Y0, 8, "x", "south", "oak")
        cart(d, 50, 12, "z")
        put(d, 53, Y0, 16, "hay_block[axis=y]")
        put(d, 48, Y0, 16, "hay_block[axis=y]")
        d.sign(51, 5, 7, "north", ["AMBULANCE"], "oak")
    return d


def hosp_neoterra(rel, L):
    d = new("Neoterra", rel, (53, 45, 51), paving="smooth_stone")
    Q = "smooth_quartz"
    cnf = 1 if L == 1 else 2
    c = bldg(d, 14, 8, 28, 18, cnf, "flat", glassy=True, win="nsw")
    ext_door(d, 20, Y0, 8, "south", double=True)
    for x in range(17, 25):
        for z in range(4, 8):
            put(d, x, 6, z, slab("smooth_quartz_slab", "top"))
    d.sign(21, 6, 3, "north", ["MEDICAL", "CENTRE"], "birch", glow=True, color="lime") if False else \
        d.sign(21, 5, 7, "north", ["MEDICAL", "CENTRE"], "birch", glow=True, color="lime")
    cy = 4 + 5 * cnf
    for k in (-1, 0, 1):                                            # glowing cross on the facade / roof
        d.set(26 + k, cy, 7 if cnf > 1 else 9, "red_concrete")
        d.set(26, cy + k, 7 if cnf > 1 else 9, "red_concrete")
    d.set(26, cy, 7 if cnf > 1 else 9, "sea_lantern")
    d.hut(15, Y0, 9)
    keep(d, 16, Y0, 9)
    for x in range(17, 22):
        d.set(x, Y0, 12, Q)
    d.chair(19, Y0, 13, "south", "mangrove", sit=False)
    put(d, 18, Y0 + 1, 12, "end_rod[facing=up]")
    line_items(d, 27, 9, "z", Y0, "west", ["brewing_stand", "furnace", "water_cauldron"] +
               (["rack"] if d.req["racks"] else []) + ["barrel"] * need(d, "barrel"))
    if d.req["seats"]:
        d.chair(15, Y0, 13, "west", "mangrove")
        d.chair(15, Y0, 14, "west", "mangrove")
        put(d, 15, Y0, 15, "potted_bamboo")
    # treatment bay behind a glass screen
    for x in range(15, 28):
        if x != 21:
            d.set(x, Y0, 16, "white_stained_glass_pane")
            d.set(x, Y0 + 1, 16, "white_stained_glass_pane")
    ward(d, (15, 17, 26, 17), Y0, min(beds_left(d), 2), head=("s",))
    for x in range(16, 27, 4):
        put(d, x, Y0, 17, "potted_bamboo") if False else None
    path(d, 19, 0, 22, 7, "polished_diorite")
    for x in (12, 30):
        post_lamp(d, x, 5)
        put(d, x + (1 if x == 12 else -1), 2, 3, "moss_block")
        put(d, x + (1 if x == 12 else -1), 3, 3, "flowering_azalea")
    if cnf > 1:
        stair_up(d, 15, 11, Y0, 7, "south") if False else stair_up(d, 22, 15, Y0, 7, "east")
        ward(d, (15, 9, 27, 17), 7, min(beds_left(d), 6), head=("n", "s"))
        put(d, 20, 7, 13, Q)
        put(d, 21, 7, 13, Q)
        d.chair(20, 7, 14, "south", "mangrove", sit=False)
        roof_garden(d, c, "garden" if L < 5 else "garden")
    if L >= 3:
        e = bldg(d, 28, 8, 42, 18, 2, "flat", glassy=True, win="nse")
        link(d, 28, Y0, 17, "east")
        link(d, 28, 7, 12, "east")
        lounge(d, (29, 9, 41, 17), Y0)
        table_set(d, (29, 9, 41, 17), Y0, "study", sit=False)
        ward(d, (29, 9, 41, 17), 7, beds_left(d), head=("n", "s"), color="lime")
        roof_garden(d, e, "solar")
        d.sign(35, 6, 7, "north", ["OUTPATIENTS"], "birch", glow=True, color="lime")
    if L >= 4:
        tnf = 4 if L == 4 else 7
        t = bldg(d, 14, 18, 28, 30, tnf, "flat", glassy=True, win="esw")
        link(d, 21, Y0, 18, "south")
        for k in range(tnf - 1):
            stair_up(d, 15 if k % 2 == 0 else 27, 19 if k % 2 == 0 else 29, Y0 + 5 * k, Y0 + 5 * k + 5,
                     "south" if k % 2 == 0 else "north")
        # surgery on the ground floor
        d.set(21, Y0, 24, "white_concrete")
        d.set(21, Y0, 25, "white_concrete")
        for x in range(17, 26):
            put(d, x, Y0, 29, ("water_cauldron[level=3]", slab("smooth_quartz_slab", "top"),
                               "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")[x % 3])
        d.sign(21, Y0 + 2, 19, "south", ["SURGERY"], "birch", glow=True, color="lime") if False else None
        for k in range(1, tnf):
            y = Y0 + 5 * k
            if k % 2:
                ward(d, (16, 20, 26, 28), y, 6, head=("w", "e"), color="cyan")
            else:
                office(d, (16, 20, 26, 28), y)
        if tnf >= 7:
            ry = t["top"] + 2
            for x in range(16, 27):
                for z in range(20, 29):
                    d.set(x, ry - 1, z, "gray_concrete")
            for i, row in enumerate(["#...#", "#...#", "#####", "#...#", "#...#"]):
                for j, ch in enumerate(row):
                    if ch == "#":
                        d.set(19 + j, ry - 1, 22 + i, "white_concrete")
            for x, z in ((16, 20), (26, 20), (16, 28), (26, 28)):
                d.set(x, ry, z, "end_rod[facing=up]")
        else:
            roof_garden(d, t, "solar")
        # ambulance bay canopy
        for x in range(30, 42):
            for z in range(20, 27):
                d.set(x, 1, z, "polished_andesite")
                put(d, x, 6, z, slab("smooth_quartz_slab", "top"))
            if x % 4 == 2:
                for y in range(Y0, 6):
                    put(d, x, y, 26, "light_gray_concrete")
        for z in range(20, 27, 2):
            d.set(36, 1, z, "yellow_concrete")
        link(d, 28, Y0, 23, "east")
    if L >= 5:
        r = bldg(d, 2, 8, 14, 30, 3, "flat", glassy=True, win="nsw")
        link(d, 14, Y0, 12, "west")
        stair_up(d, 3, 28, Y0, 7, "north")
        stair_up(d, 13, 28, 7, 12, "north")
        for y in (Y0, 7, 12):
            lab(d, (3, 9, 13, 16), y)
            table_set(d, (3, 18, 13, 26), y, "study", sit=False)
        roof_garden(d, r, "garden")
        d.sign(8, 6, 7, "north", ["RESEARCH"], "birch", glow=True, color="lime")
        # healing garden
        lawn(d, 2, 32, 50, 49)
        path(d, 2, 40, 50, 41, "polished_diorite")
        for x in range(4, 50, 6):
            flowerbed(d, x, 34, x + 3, 36, ("allium", "azure_bluet", "white_tulip", "cornflower"))
            plant_tree(d, x + 2, 45)
        for x in range(6, 48, 8):
            park_bench(d, x, 42, "x", "south")
        fountain(d, 26, 40, 2)
    return d


def hosp_cascadia(rel, L):
    d = new("Cascadia", rel, (55, 30, 53), paving="coarse_dirt")
    cnf = 2 if L >= 3 else 1
    c = bldg(d, 6, 6, 16, 16, cnf, "gable", "z")
    ext_door(d, 11, Y0, 6, "south")
    d.fill(5, 1, 1, 17, 1, 5, "spruce_planks")
    for x in (5, 9, 13, 17):
        for y in range(Y0, 5):
            put(d, x, y, 1, log("spruce_log"))
    for x in range(4, 19):
        d.set(x, 5, 0, st("spruce_stairs", "south"))
        for z in range(1, 6):
            d.set(x, 5, z, slab("spruce_slab"))
    d.sign(11, 4, 5, "north", ["INFIRMARY", "+"], "spruce")
    if d.req["seats"]:
        d.chair(6, Y0, 3, "west", "spruce")
        d.chair(16, Y0, 3, "east", "spruce")
    d.hut(7, Y0, 7)
    keep(d, 8, Y0, 7)
    line_items(d, 15, 7, "z", Y0, "west", ["brewing_stand", "furnace", "water_cauldron"] +
               (["rack"] if d.req["racks"] else []))
    line_items(d, 9, 15, "x", Y0, "north", ["barrel"] * need(d, "barrel"))
    for x in (9, 10, 11):
        put(d, x, Y0, 10, slab("spruce_slab", "top"))
    d.chair(10, Y0, 11, "south", "spruce", sit=False)
    chimney(d, 6, 13, Y0, c["ridge"] + 1)
    d.hearth(7, Y0, 13, "east", 6, "cobblestone", "campfire")
    if L == 1:
        ward(d, (8, 14, 13, 15), Y0, beds_left(d), head=("s",), color="white")
    if cnf > 1:
        stair_up(d, 9, 15, Y0, 7, "east") if False else stair_up(d, 8, 13, Y0, 7, "east")
        office(d, (7, 7, 15, 11), 7)
        dorm(d, (7, 14, 15, 15), 7, 0, head="s") if False else lounge(d, (7, 12, 15, 15), 7)
    if L >= 2:
        wx2 = 30 if L == 2 else 36
        w = bldg(d, 16, 8, wx2, 16, 1, "gable", "x", win="nse")
        link(d, 16, Y0, 12, "east")
        n_here = min(beds_left(d), 4 if L == 2 else 8)
        ward(d, (17, 9, wx2 - 1, 15), Y0, n_here, head=("n", "s"), color="white")
        chimney(d, wx2, 12, Y0, w["ridge"] + 1)
    if L >= 3:
        # screened sleeping porch along the ward
        for x in range(16, wx2 + 1):
            for z in range(17, 21):
                d.set(x, 1, z, "spruce_planks")
                d.set(x, 6, z, slab("spruce_slab"))
            if x % 4 == 0:
                for y in range(Y0, 6):
                    d.set(x, y, 20, log("spruce_log"))
            else:
                d.set(x, Y0, 20, "spruce_fence")
        d.door(22, Y0, 16, "south", "spruce")
        for x in (18, 24, 30, 33):
            d.chair(x, Y0, 18, "north", "spruce", sit=False)
            put(d, x + 1, Y0, 18, slab("spruce_slab", "top"))
    if L >= 4:
        sz1 = 26
        sn = bldg(d, 6, sz1, 40, sz1 + 8, 2, "gable", "x")
        ext_door(d, 23, Y0, sz1, "south", double=True)
        path(d, 23, 21, 24, sz1 - 1, "spruce_planks", border=False)
        stair_up(d, 7, sz1 + 7, Y0, 7, "east")
        ward(d, (14, sz1 + 1, 39, sz1 + 7), Y0, max(beds_left(d), 4), head=("n", "s"), color="green")
        lounge(d, (7, sz1 + 1, 13, sz1 + 6), Y0)
        dorm(d, (14, sz1 + 1, 39, sz1 + 7), 7, 8, head="s", color="white")
        office(d, (7, sz1 + 1, 13, sz1 + 5), 7, desk_side="s")
        for x in range(6, 41):                                      # long verandah
            for z in range(sz1 + 9, sz1 + 12):
                d.set(x, 1, z, "spruce_planks")
                d.set(x, 6, z, slab("spruce_slab"))
            if x % 4 == 2:
                for y in range(Y0, 6):
                    d.set(x, y, sz1 + 11, log("spruce_log"))
        for x in range(8, 40, 4):
            d.chair(x, Y0, sz1 + 10, "south", "spruce", sit=False)
        d.door(23, Y0, sz1 + 8, "north", "spruce")
        chimney(d, 40, sz1 + 4, Y0, 16)
    if L >= 5:
        dh = bldg(d, 40, 4, 50, 14, 2, "gable", "z", mat="mangrove_planks", up="mangrove_planks")
        ext_door(d, 45, Y0, 4, "south")
        stair_up(d, 49, 6, Y0, 7, "south")
        lounge(d, (41, 5, 48, 9), Y0)
        kitchen(d, (41, 10, 49, 13), Y0)
        dorm(d, (41, 5, 49, 13), 7, 2, head="w", color="red")
        d.sign(45, 5, 3, "north", ["DOCTOR"], "spruce")
        # laundry & boiler house with a tall stack
        lh = bldg(d, 42, 18, 50, 24, 1, "gable", "x", mat="cobblestone", up="cobblestone", gable_end="cobblestone")
        ext_door(d, 46, Y0, 18, "south")
        for x in range(43, 50, 2):
            put(d, x, Y0, 23, "water_cauldron[level=3]")
        for x in range(43, 50):
            put(d, x, 4, 21, "white_wool" if x % 2 else "light_blue_wool") if False else None
        chimney(d, 50, 21, Y0, 16)
        # glasshouse + herb garden
        for x in range(42, 53):
            for z in range(38, 47):
                edge = x in (42, 52) or z in (38, 46)
                if edge:
                    for y in range(Y0, 5):
                        d.set(x, y, z, "glass" if (x + z) % 3 else log("spruce_log"))
                else:
                    d.set(x, 1, z, "farmland[moisture=7]" if (x + z) % 2 else "spruce_planks")
                    if (x + z) % 2:
                        d.set(x, Y0, z, ("fern", "sweet_berry_bush[age=2]", "potted_fern")[x % 2])
                d.set(x, 5, z, "glass")
        d.set(47, Y0, 38, AIR)
        d.set(47, Y0 + 1, 38, AIR)
        d.door(47, Y0, 38, "south", "spruce")
        ws = bldg(d, 28, 40, 38, 46, 1, "gable", "x", mat="stripped_spruce_log", win="")
        ext_door(d, 33, Y0, 40, "south", double=True)
        for x in range(29, 38):
            for y in (Y0, Y0 + 1):
                if x not in (33, 34):
                    put(d, x, y, 45, log("spruce_log", "z"))
        workshop(d, (29, 41, 37, 44), Y0)
        d.sign(33, 5, 39, "north", ["WOODSHED"], "spruce")
        for x in range(1, 40, 3):
            plant_tree(d, x, 48) if x % 6 == 1 else flowerbed(d, x, 47, x + 1, 48, ("fern", "blue_orchid", "allium", "lily_of_the_valley"))
    return d


@design("hospital")
def hospital_v2(pack, rel, L):
    return common_materials({"Hearthwood": hosp_hearthwood, "Cascadia": hosp_cascadia, "Neoterra": hosp_neoterra}[pack](rel, L))


# ============================================================================================ LIBRARY v2
def stall_row(d, x1, x2, z, y, h, face_desk=None):
    """Oxford-style press: a double-sided bookcase run along x with reading desks at its ends."""
    for x in range(x1, x2 + 1):
        for k in range(h):
            if d.air(x, y + k, z) and (x, y + k, z) not in d.res:
                d.bookshelf(x, y + k, z)


def lib_hearthwood(rel, L):
    d = new("Hearthwood", rel, (49, 34, 55))
    SS = "smooth_sandstone"
    hnf = 2 if L >= 3 else 1
    h = bldg(d, 16, 8, 30, 20, hnf, "gable", "x", win="nsew", ws=2)
    ext_door(d, 23, Y0, 8, "south")
    d.sign(23, 5, 7, "north", ["LIBRARY", "", "Sapere aude"], "dark_oak")
    for x in (21, 25):                                              # columned porch
        for y in range(Y0, 6):
            put(d, x, y, 5, "quartz_pillar[axis=y]")
    d.fill(21, 6, 5, 25, 6, 7, "cut_sandstone")
    for x in range(21, 26):
        d.set(x, 7, 5, st("sandstone_stairs", "south"))
    d.fill(21, 1, 4, 25, 1, 7, "cut_sandstone")
    d.hut(17, Y0, 9)
    keep(d, 18, Y0, 9)
    d.item(23, Y0, 18, "lectern", "north")
    keep(d, 23, Y0, 17)
    # stalls from both long walls with reading desks in the window bays
    for z in (11, 15):
        stall_row(d, 17, 19, z, Y0, 3)
        stall_row(d, 27, 29, z, Y0, 3)
    for z in (12, 13, 16, 17):
        desk(d, 17, Y0, z, "east")
        desk(d, 29, Y0, z, "west")
    for z in range(9, 20):
        put(d, 23, Y0, z, "red_carpet")
    rug_in(d, (21, 10, 25, 19), Y0, ("red_carpet", "green_carpet"))
    if hnf > 1:
        stair_up(d, 21, 19, Y0, 7, "west") if False else stair_up(d, 20, 19, Y0, 7, "east")
        shelf_wall(d, (17, 9, 29, 19), "n", 7, 3)
        shelf_wall(d, (17, 9, 29, 19), "w", 7, 3)
        shelf_wall(d, (17, 9, 29, 19), "e", 7, 3)
        long_table(d, 21, 13, 25, 7, "dark_oak")
        lights(d, (17, 9, 29, 19), 7)
    for x in (14, 32):
        post_lamp(d, x, 5)
    hedge(d, 16, 2, 20, 2)
    hedge(d, 26, 2, 30, 2)
    flowerbed(d, 16, 3, 20, 4)
    flowerbed(d, 26, 3, 30, 4)
    if L >= 2:
        swnf = 2 if L >= 4 else 1
        sw = bldg(d, 30, 9, 42, 19, swnf, "gable", "z", win="nse")
        link(d, 30, Y0, 14, "east")
        for z in range(10, 19, 3):
            stall_row(d, 32, 40, z, Y0, 3)
        if swnf > 1:
            stair_up(d, 41, 10, Y0, 7, "south")
            office(d, (31, 10, 40, 18), 7)
            table_set(d, (31, 10, 40, 18), 7, "study", sit=False)
        d.sign(36, 5, 8, "north", ["STACKS"], "dark_oak")
        chimney(d, 42, 14, Y0, sw["ridge"] + 1)
    if L >= 4:
        # the rotunda (Radcliffe-style domed reading room) behind the hall
        cx, cz, R = 23, 30, 7
        for y in range(Y0, 11):
            for x in range(cx - R, cx + R + 1):
                for z in range(cz - R, cz + R + 1):
                    dd = (x - cx) ** 2 + (z - cz) ** 2
                    if (R - 0.5) ** 2 <= dd <= (R + 0.5) ** 2:
                        d.set(x, y, z, SS if not (y in (4, 5, 6, 7) and (x + z) % 3 == 0) else "glass_pane")
                    elif dd < (R - 0.5) ** 2:
                        d.set(x, y, z, AIR)
                        if y == Y0:
                            d.set(x, 1, z, "polished_andesite" if (x + z) % 2 else "smooth_stone")
        for k in range(0, R + 1):                                   # stepped dome
            y = 11 + k
            r = R - k
            for x in range(cx - R, cx + R + 1):
                for z in range(cz - R, cz + R + 1):
                    dd = (x - cx) ** 2 + (z - cz) ** 2
                    if (r - 0.6) ** 2 <= dd <= (r + 0.6) ** 2 or (r <= 0 and dd == 0):
                        d.set(x, y, z, "mud_bricks" if k < R - 1 else "cut_sandstone")
        d.set(cx, 11 + R + 1, cz, "lantern[hanging=false,waterlogged=false]")
        d.fill(cx - 1, Y0, cz + R, cx + 1, 4, cz + R, AIR)
        for x in range(cx - 1, cx + 2):
            for z in range(cz + 2, cz + R + 2):
                keep(d, x, Y0, z, 3)
        d.fill(cx - 1, Y0, cz - R, cx + 1, 4, cz - R, AIR)
        d.fill(cx - 1, Y0, h["z2"], cx + 1, 4, h["z2"], AIR)
        for x in range(cx - 1, cx + 2):
            for z in range(h["z2"], cz - 1):
                d.set(x, 1, z, "polished_andesite")
                keep(d, x, Y0, z, 3)
        for z in range(h["z2"] + 1, cz - R):
            for x in (cx - 2, cx + 2):
                for y in range(Y0, 6):
                    d.set(x, y, z, SS)
            for x in range(cx - 2, cx + 3):
                d.set(x, 6, z, "cut_sandstone")
        for x in range(cx - R + 1, cx + R):                          # radial presses
            for z in range(cz - R + 1, cz + R):
                dd = (x - cx) ** 2 + (z - cz) ** 2
                if (R - 1.5) ** 2 <= dd < (R - 0.5) ** 2 and (x, Y0, z) not in d.res:
                    for k in range(4):
                        if d.air(x, Y0 + k, z):
                            d.bookshelf(x, Y0 + k, z)
        d.item(cx, Y0, cz, "enchanting_table")
        for x, z, b in ((cx - 2, cz, "east"), (cx + 2, cz, "west"), (cx, cz + 2, "south")):
            put(d, x, Y0, z, slab("dark_oak_slab", "top"))
        for x, z, back in ((cx - 3, cz, "west"), (cx + 3, cz, "east"), (cx, cz + 3, "south"), (cx - 3, cz + 2, "west"),
                           (cx + 3, cz + 2, "east"), (cx - 2, cz + 3, "south"), (cx + 2, cz + 3, "south")):
            if d.air(x, Y0, z):
                d.chair(x, Y0, z, back, "dark_oak")
        for z in range(cz - 4, cz + 5, 4):
            put(d, cx, 10, z, "chain[axis=y,waterlogged=false]")
            put(d, cx, 9, z, "lantern[hanging=true,waterlogged=false]")
    if L >= 5:
        # manuscripts wing (two storeys) + cloister garden + librarian's cottage
        mw = bldg(d, 4, 9, 16, 21, 2, "gable", "z", win="nsw", mat="smooth_sandstone", up="calcite")
        link(d, 16, Y0, 14, "west")
        stair_up(d, 5, 20, Y0, 7, "north")
        for z in range(10, 20, 3):
            stall_row(d, 7, 14, z, Y0, 2)
        office(d, (5, 10, 15, 20), 7)
        table_set(d, (5, 10, 15, 20), 7, "study", sit=False)
        lawn(d, 2, 24, 14, 44)
        for x in range(2, 15):
            put(d, x, 2, 44, "sandstone_wall")
        for z in range(24, 45):
            put(d, 2, 2, z, "sandstone_wall")
        path(d, 8, 23, 9, 43)
        for z in range(26, 43, 4):
            flowerbed(d, 4, z, 6, z + 1)
            flowerbed(d, 11, z, 13, z + 1)
        plant_tree(d, 5, 40)
        plant_tree(d, 12, 32)
        lc = bldg(d, 34, 34, 44, 44, 2, "gable", "x", mat="calcite", up="calcite")
        ext_door(d, 39, Y0, 34, "south")
        stair_up(d, 35, 43, Y0, 7, "east")
        lounge(d, (35, 35, 43, 39), Y0)
        kitchen(d, (35, 40, 43, 43), Y0)
        dorm(d, (35, 35, 43, 43), 7, 2, head="n")
        chimney(d, 44, 39, Y0, lc["ridge"] + 1)
        flowerbed(d, 35, 30, 43, 32)
        for x in range(34, 45):
            put(d, x, 2, 29, "dark_oak_fence")
    shelf_runs(d, [], 0)
    return d


def lib_neoterra(rel, L):
    d = new("Neoterra", rel, (51, 45, 51), paving="smooth_stone")
    Q = "smooth_quartz"
    nf = 2 if L >= 3 else 1
    p = bldg(d, 16, 8, 30, 18, nf, "flat", glassy=True, win="nsew")
    ext_door(d, 22, Y0, 8, "south", double=True)
    d.sign(22, 6, 7, "north", ["PUBLIC", "LIBRARY"], "birch", glow=True, color="orange")
    d.sign(23, 6, 7, "north", ["", "open late"], "birch", glow=True, color="orange")
    for x in range(19, 28):
        for z in range(4, 8):
            put(d, x, 6, z, slab("smooth_quartz_slab", "top"))
    d.hut(17, Y0, 9)
    keep(d, 18, Y0, 9)
    for x in range(25, 29):
        d.set(x, Y0, 11, Q)
    d.item(26, Y0, 10, "lectern", "north")
    keep(d, 26, Y0, 9)
    d.chair(27, Y0, 12, "south", "mangrove", sit=False)
    for tz in (14,):
        for tx in range(19, 24):
            d.table(tx, Y0, tz, "birch", "block", Q)
            d.chair(tx, Y0, tz - 1, "north", "mangrove")
            d.chair(tx, Y0, tz + 1, "south", "mangrove")
    shelf_wall(d, (17, 9, 29, 17), "s", Y0, 3)
    shelf_wall(d, (17, 9, 29, 17), "w", Y0, 2, skip=[(17, 9)])
    corners(d, (17, 9, 29, 17), Y0, ["potted_bamboo"])
    for x in (13, 33):
        post_lamp(d, x, 5)
        put(d, x, 2, 3, "moss_block")
        put(d, x, 3, 3, "flowering_azalea")
    if nf > 1:
        stair_up(d, 29, 12, Y0, 7, "south") if False else stair_up(d, 28, 16, Y0, 7, "west")
        for z in (10, 13):
            stall_row(d, 18, 26, z, 7, 3)
        shelf_wall(d, (17, 9, 29, 17), "w", 7, 3)
        lights(d, (17, 9, 29, 17), 7)
        roof_garden(d, p, "garden")
    if L >= 2:
        sb = bldg(d, 30, 8, 40, 18, nf, "flat", glassy=False, win="ns", mat="orange_terracotta", up="orange_terracotta")
        link(d, 30, Y0, 13, "east")
        for z in (10, 12, 15, 17):
            stall_row(d, 32, 38, z, Y0, 3)
        if nf > 1:
            link(d, 30, 7, 13, "east")
            for z in (10, 12, 15, 17):
                stall_row(d, 32, 38, z, 7, 3)
            roof_garden(d, sb, "solar")
        d.sign(35, 6, 7, "north", ["STACKS"], "birch", glow=True, color="orange")
    if L >= 4:
        tw = bldg(d, 16, 18, 28, 32, 5, "flat", glassy=True, win="esw")
        link(d, 22, Y0, 18, "south")
        for k in range(4):
            stair_up(d, 17 if k % 2 == 0 else 27, 19 if k % 2 == 0 else 31, Y0 + 5 * k, Y0 + 5 * k + 5,
                     "south" if k % 2 == 0 else "north")
        d.item(22, Y0, 25, "enchanting_table")
        for x, z, back in ((20, 25, "west"), (24, 25, "east"), (22, 27, "south"), (22, 23, "north")):
            d.chair(x, Y0, z, back, "mangrove")
        rug_in(d, (19, 22, 25, 28), Y0, ("orange_carpet", "white_carpet"), inset=0)
        for k in range(1, 5):
            y = Y0 + 5 * k
            for z in (21, 24, 27, 30):
                stall_row(d, 19, 25, z, y, 2 if k % 2 else 3)
            lights(d, (17, 19, 27, 31), y)
        roof_garden(d, tw, "garden")
        d.sign(22, 6, 33, "south", ["MEDIA", "TOWER"], "birch", glow=True, color="orange")
    if L >= 5:
        au = bldg(d, 30, 20, 46, 32, 2, "flat", wh=6, win="e")
        stair_up(d, 45, 22, Y0, 8, "south")
        table_set(d, (31, 21, 45, 31), 8, "study", sit=False)
        link(d, 28, Y0, 26, "east") if False else ext_door(d, 38, Y0, 32, "north", double=True)
        lecture(d, (31, 21, 44, 31), Y0, "n", h=6)
        roof_garden(d, au, "garden")
        lawn(d, 2, 34, 48, 49)
        path(d, 2, 40, 48, 41, "polished_diorite")
        for x in range(4, 48, 7):
            plant_tree(d, x, 37)
            park_bench(d, x + 2, 43, "x", "south")
            flowerbed(d, x, 46, x + 3, 47, ("allium", "azure_bluet", "white_tulip", "orange_tulip"))
            post_lamp(d, x + 5, 39)
        # café kiosk
        ck = bldg(d, 4, 8, 12, 16, 1, "flat", glassy=True, win="nse")
        ext_door(d, 8, Y0, 8, "south")
        kitchen(d, (5, 9, 11, 10), Y0)
        table_set(d, (5, 11, 11, 15), Y0, "dining")
        for x in range(4, 13):
            for z in range(4, 8):
                put(d, x, 6, z, f"{('orange' if x % 2 else 'white')}_concrete" if z == 4 else slab("smooth_quartz_slab", "top"))
        d.sign(8, 6, 7, "north", ["CAFE"], "birch", glow=True, color="orange") if False else None
    return d


def aframe(d, x1, z1, x2, z2, roof=None, glaze_front=True):
    """A-frame: roof from the ground up, glazed log-framed street gable, plank back gable."""
    roof = roof or d.S["roof"]
    d.fill(x1, 1, z1, x2, 1, z2, "spruce_planks")
    ridge = d.gable(x1, z1, x2, z2, Y0, "z", f"{roof}_stairs", f"{roof}_slab", "spruce_planks", overhang=1)
    if glaze_front:
        for x in range(x1 + 1, x2):
            for y in range(Y0, ridge):
                if d.get(x, y, z1) == "minecraft:spruce_planks":
                    d.set(x, y, z1, "glass_pane" if (x - x1) % 3 else log("spruce_log"))
        for x in range(x1 + 1, x2):
            if d.get(x, 6, z1).startswith(("minecraft:glass_pane", "minecraft:spruce_log")):
                d.set(x, 6, z1, log("spruce_log", "x"))
    return ridge


def lib_cascadia(rel, L):
    d = new("Cascadia", rel, (55, 30, 55), paving="coarse_dirt")
    X1, X2, Z1, Z2 = 16, 34, 6, 18
    ridge = aframe(d, X1, Z1, X2, Z2)
    mid = (X1 + X2) // 2
    d.double_door(mid, Y0, Z1, "x", "south", "spruce")
    keep(d, mid, Y0, Z1 + 1, 3)
    keep(d, mid + 1, Y0, Z1 + 1, 3)
    d.sign(mid, 8, Z1 - 1, "north", ["READING", "LODGE"], "spruce")
    for x in range(X1, X2 + 1):                                     # front deck
        for z in range(Z1 - 4, Z1):
            d.set(x, 1, z, "spruce_planks")
        if abs(x - mid - 0.5) > 1.5:
            put(d, x, Y0, Z1 - 4, "spruce_fence")
    for y in range(Y0, ridge + 2):
        for x in (mid, mid + 1):
            if y < ridge - 1 or x == mid:
                d.set(x, y, Z2, "cobblestone" if (x + y) % 3 else "mossy_cobblestone")
    d.hearth(mid, Y0, Z2 - 1, "north", ridge + 1, "cobblestone", "campfire")
    d.hut(X1 + 4, Y0, Z1 + 1)
    keep(d, X1 + 5, Y0, Z1 + 1)
    d.item(X2 - 4, Y0, Z1 + 1, "lectern", "west")
    keep(d, X2 - 5, Y0, Z1 + 1)
    for z in range(Z1 + 1, Z2):                                      # eave stacks
        for (x, hh) in ((X1 + 1, 1), (X1 + 2, 2), (X1 + 3, 3), (X2 - 1, 1), (X2 - 2, 2), (X2 - 3, 3)):
            if (x, Y0, z) not in d.res:
                for k in range(hh):
                    if d.air(x, Y0 + k, z):
                        d.bookshelf(x, Y0 + k, z)
    for z in (Z1 + 3, Z1 + 6):
        for tx in (mid - 3, mid + 4):
            d.table(tx, Y0, z, "spruce", "post")
            d.chair(tx - 1, Y0, z, "west", "spruce")
            d.chair(tx + 1, Y0, z, "east", "spruce")
    rug_in(d, (mid - 1, Z1 + 2, mid + 2, Z2 - 3), Y0, ("brown_carpet", "green_carpet"), inset=0)
    for z in range(Z1 + 2, Z2 - 1, 4):
        for x in range(X1 + 7, X2 - 6):
            d.set(x, 9, z, log("stripped_spruce_log", "x"))
        d.set(mid, 8, z, "lantern[hanging=true,waterlogged=false]")
    for x in (X1 - 2, X2 + 2):
        post_lamp(d, x, Z1 - 2)
    if L >= 2:
        # children's A-frame on the east, joined by a covered walk
        r2 = aframe(d, 38, 8, 50, 16)
        d.door(44, Y0, 8, "south", "spruce")
        keep(d, 44, Y0, 9, 3)
        for z in range(9, 16):
            for (x, hh) in ((39, 1), (40, 2), (49, 1), (48, 2)):
                for k in range(hh):
                    if d.air(x, Y0 + k, z):
                        d.bookshelf(x, Y0 + k, z)
        rug_in(d, (42, 10, 46, 14), Y0, ("lime_carpet", "yellow_carpet", "light_blue_carpet"), inset=0, pattern="border")
        for x in (42, 46):
            d.chair(x, Y0, 15, "south", "spruce", sit=False)
        d.sign(44, 7, 7, "north", ["STORY", "CORNER"], "spruce")
        for x in (37, 51):
            post_lamp(d, x, 6)
        flowerbed(d, 38, 5, 41, 6, ("fern", "blue_orchid", "allium", "dandelion"))
        flowerbed(d, 47, 5, 50, 6, ("fern", "blue_orchid", "allium", "dandelion"))
        for x in range(35, 38):
            for z in range(10, 14):
                d.set(x, 1, z, "spruce_planks")
                d.set(x, 6, z, slab("spruce_slab"))
        for x in (35, 37):
            for z in (10, 13):
                for y in range(Y0, 6):
                    d.set(x, y, z, log("spruce_log"))
        cx, cz = 44, 3                                              # story fire circle
        d.set(cx, Y0, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        for (x, z, ax) in ((cx - 2, cz, "z"), (cx + 2, cz, "z"), (cx, cz - 2, "x")):
            d.set(x, Y0, z, log("stripped_spruce_log", ax))
        for x in range(cx - 2, cx + 3):
            for z in range(cz - 2, cz + 3):
                if d.get(x, 1, z) == "minecraft:coarse_dirt":
                    d.set(x, 1, z, "gravel")
    if L >= 3:
        ar = bldg(d, 2, 6, 12, 18, 2, "gable", "z")
        ext_door(d, 7, Y0, 6, "south")
        d.sign(7, 5, 5, "north", ["ARCHIVE"], "spruce")
        stair_up(d, 11, 8, Y0, 7, "south")
        for z in range(8, 18, 3):
            stall_row(d, 3, 8, z, Y0, 3)
        for z in range(8, 18, 3):
            stall_row(d, 3, 9, z, 7, 2)
        lights(d, (3, 7, 11, 17), 7)
        chimney(d, 2, 12, Y0, 15)
    if L >= 4:
        sh = bldg(d, 8, 24, 44, 34, 2, "gable", "x", ws=3)
        ext_door(d, 26, Y0, 24, "south", double=True)
        path(d, 26, 19, 27, 23, "spruce_planks", border=False)
        stair_up(d, 9, 33, Y0, 7, "east")
        for x in range(12, 44, 4):
            for xx in (x, x + 1):
                for z in range(26, 33):
                    if (xx, Y0, z) not in d.res and d.air(xx, Y0, z) and abs(xx - 26.5) > 2:
                        for k in range(3):
                            d.bookshelf(xx, Y0 + k, z)
        d.item(26, Y0, 30, "enchanting_table")
        for x in range(9, 44):
            for z in (25, 33):
                if (x, 7, z) not in d.res and d.air(x, 7, z):
                    d.bookshelf(x, 7, z)
        table_set(d, (10, 26, 43, 32), 7, "dining")
        chimney(d, 44, 29, Y0, 16)
        d.sign(26, 6, 23, "north", ["THE STACKS"], "spruce")
    if L >= 5:
        # librarian's cabin, a lookout deck and a reading garden
        cb = bldg(d, 44, 40, 52, 50, 2, "gable", "z", mat="mangrove_planks", up="mangrove_planks")
        ext_door(d, 48, Y0, 40, "south")
        lounge(d, (45, 41, 51, 45), Y0)
        kitchen(d, (45, 46, 51, 49), Y0)
        stair_up(d, 51, 42, Y0, 7, "south")
        dorm(d, (45, 41, 51, 49), 7, 2, head="w")
        chimney(d, 52, 45, Y0, 17)
        # bookbindery & print shop
        bb = bldg(d, 2, 38, 16, 52, 2, "gable", "z", mat="stripped_dark_oak_log", up="stripped_dark_oak_log")
        ext_door(d, 9, Y0, 38, "south", double=True)
        d.sign(9, 5, 37, "north", ["BINDERY"], "spruce")
        workshop(d, (3, 39, 15, 45), Y0)
        for z in (48, 50):
            stall_row(d, 4, 11, z, Y0, 2)
        stair_up(d, 15, 40, Y0, 7, "south") if False else stair_up(d, 3, 46, Y0, 7, "north") if False else None
        stair_up(d, 14, 47, Y0, 7, "north")
        table_set(d, (3, 39, 15, 51), 7, "study", sit=False)
        for z in range(40, 52, 3):
            stall_row(d, 4, 8, z, 7, 2)
        chimney(d, 16, 45, Y0, 18)
        for x in range(4, 42):
            for z in range(38, 52):
                if (x * 3 + z) % 9 == 0:
                    d.set(x, 1, z, "moss_block")
        for x in range(6, 40, 6):
            plant_tree(d, x, 48)
            park_bench(d, x + 2, 42, "x", "south")
        for x in range(4, 42):
            put(d, x, 2, 37, "spruce_fence") if x % 8 else None
        dk = (20, 40, 32, 46)
        for x in range(dk[0], dk[2] + 1):
            for z in range(dk[1], dk[3] + 1):
                d.set(x, 4, z, "spruce_planks")
                if x in (dk[0], dk[2]) or z in (dk[1], dk[3]):
                    d.set(x, 5, z, "spruce_fence")
        for x, z in ((dk[0], dk[1]), (dk[2], dk[1]), (dk[0], dk[3]), (dk[2], dk[3])):
            for y in range(Y0, 4):
                d.set(x, y, z, log("spruce_log"))
        for k in range(3):
            d.set(dk[0] + 3 + k, Y0 + k, dk[1] - 1, st("spruce_stairs", "east")) if False else None
        for z in range(dk[1] + 1, dk[3]):
            for x in range(dk[0] + 1, dk[2]):
                if (x + z) % 4 == 0:
                    d.chair(x, 5, z, "south", "spruce", sit=False)
    return d


@design("library")
def library_v2(pack, rel, L):
    return common_materials({"Hearthwood": lib_hearthwood, "Cascadia": lib_cascadia, "Neoterra": lib_neoterra}[pack](rel, L))


# ============================================================================================ SCHOOL v2
def art_room(d, r, y):
    """Art room: the loom and map table (L3+ requirement), easels, paint table, drying line."""
    x1, z1, x2, z2 = r
    if need(d, "loom"):
        line_items(d, x1, z1, "x", y, "south", ["loom", None, "cartography_table"])
    wood = d.S["wood"]
    for x in (x1 + 1, x1 + 3, x2 - 1):                               # three easels along the back wall
        put(d, x, y, z2, f"{wood}_fence")
        put(d, x, y + 1, z2, f"{wood}_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]")
    cx, cz = mid(r)
    for i, x in enumerate((cx - 1, cx, cx + 1)):                     # paint table with stools
        if put(d, x, y, cz, slab(f"{wood}_slab" if d.pack != "Neoterra" else "smooth_quartz_slab", "top")):
            put(d, x, y + 1, cz, ("flower_pot", "candle[candles=2,lit=false,waterlogged=false]",
                                  "red_candle[candles=1,lit=false,waterlogged=false]")[i])
            if d.air(x, y, cz + 1) and (x, y, cz + 1) not in d.res:
                d.chair(x, y, cz + 1, "south", wood, sit=False)
    wall_art(d, r, y, colors=("yellow", "lime", "light_blue", "pink"))
    lights(d, r, y)


def playground(d, x1, z1, x2, z2, wall=None):
    wall = wall or {"Hearthwood": "brick_wall", "Cascadia": "spruce_fence", "Neoterra": "birch_fence"}[d.pack]
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                put(d, x, 2, z, wall)
    hop = [(1, 1), (1, 2), (0, 3), (2, 3), (1, 4), (0, 5), (2, 5), (1, 6)]
    for a, b in hop:
        d.set(x1 + 2 + a, 1, z1 + 2 + b, "white_concrete" if (a + b) % 2 else "yellow_terracotta")
    sx = x2 - 4                                                     # swing set
    for z in (z1 + 2, z1 + 5):
        for y in range(2, 6):
            put(d, sx, y, z, f"{d.S['wood']}_fence" if d.pack != "Cascadia" else log("spruce_log"))
    for z in range(z1 + 2, z1 + 6):
        put(d, sx, 6, z, log("spruce_log", "z") if d.pack != "Neoterra" else "birch_planks")
    for z in (z1 + 3, z1 + 4):
        for y in (4, 5):
            put(d, sx, y, z, "chain[axis=y,waterlogged=false]")
        put(d, sx, 3, z, slab(f"{d.S['wood']}_slab", "top"))
    for x in range(x1 + 2, x1 + 5):                                  # sandpit
        for z in range(z2 - 4, z2 - 1):
            d.set(x, 1, z, "sand")


def sch_hearthwood(rel, L):
    d = new("Hearthwood", rel, (49, 28, 49))
    sr = bldg(d, 16, 8, 30, 16, 1, "gable", "x", ws=3)
    ext_door(d, 27, Y0, 8, "south")
    for x in (26, 28):
        for y in range(Y0, 5):
            put(d, x, y, 5, "oak_fence")
    d.fill(26, 5, 5, 28, 5, 7, "oak_planks")
    d.gable(26, 5, 28, 7, 6, "z", f"{d.S['roof']}_stairs", f"{d.S['roof']}_slab", "yellow_terracotta", overhang=0)
    d.sign(27, 4, 4, "north", ["VILLAGE", "SCHOOL", "est. 1872"], "oak")
    # bell-cote on the west gable
    rg = sr["ridge"]
    for z in (11, 13):
        d.set(16, rg + 1, z, "brick_wall")
    d.fill(16, rg + 2, 11, 16, rg + 2, 13, slab("brick_slab"))
    d.set(16, rg + 2, 12, "bricks")
    bell(d, 16, rg + 1, 12, "east")
    d.hut(29, Y0, 9)
    keep(d, 28, Y0, 9)
    classroom(d, (17, 9, 29, 15), Y0, board="w", need=d.req["seats"], teacher_spot=True)
    shelf_runs(d, [(29, 11, 29, 14, Y0 + 1, 1), (29, 11, 29, 14, Y0 + 2, 1)], d.req["bookshelves"])
    for z in (10, 11):
        put(d, 28, Y0 + 1, z, "oak_fence") if False else None
    chimney(d, 30, 14, Y0 + 3, rg + 1)
    flowerbed(d, 17, 5, 24, 6)
    for x in (15, 31):
        post_lamp(d, x, 6)
    path(d, 26, 0, 28, 4)
    if L >= 2:
        inf = bldg(d, 30, 8, 38, 16, 1, "gable", "z")
        link(d, 30, Y0, 12, "east")
        lounge(d, (31, 9, 37, 15), Y0)
        for x in range(31, 38, 2):
            put(d, x, Y0, 15, "white_wool" if x % 4 == 1 else "light_blue_wool")
        shelf_wall(d, (31, 9, 37, 15), "e", Y0, 1, chisel=False)
        d.sign(34, 5, 7, "north", ["INFANTS"], "oak")
        playground(d, 30, 18, 46, 30)
    if L >= 3:
        ar = bldg(d, 18, 16, 26, 25, 2, "gable", "z", mat="bricks", up="yellow_terracotta")
        link(d, 22, Y0, 16, "south")
        art_room(d, (19, 17, 25, 24), Y0)
        stair_up(d, 25, 19, Y0, 7, "south") if False else stair_up(d, 19, 20, Y0, 7, "south")
        table_set(d, (20, 17, 25, 24), 7, "study", sit=False)
        for z in range(17, 25, 2):
            put(d, 25, 7, z, "loom[facing=west]") if False else put(d, 25, 7, z, "white_wool" if z % 4 == 1 else "pink_wool")
        lights(d, (19, 17, 25, 24), 7)
        chimney(d, 26, 20, Y0, 17)
    if L >= 4:
        mh = bldg(d, 2, 6, 14, 18, 2, "gable", "z", mat="bricks", up="yellow_terracotta")
        ext_door(d, 8, Y0, 6, "south")
        d.sign(8, 5, 5, "north", ["SCHOOL", "HOUSE"], "oak")
        stair_up(d, 13, 8, Y0, 7, "south")
        lounge(d, (3, 7, 12, 11), Y0)
        kitchen(d, (3, 13, 13, 17), Y0)
        dorm(d, (3, 7, 13, 17), 7, 2, head="w", color="yellow")
        office(d, (3, 13, 12, 17), 7) if False else None
        chimney(d, 2, 12, Y0, 16)
        for x in range(1, 15):
            put(d, x, 2, 3, "oak_fence")
        flowerbed(d, 3, 4, 6, 5)
        flowerbed(d, 10, 4, 13, 5)
        hl = bldg(d, 14, 26, 30, 36, 1, "gable", "x", wh=6)
        ext_door(d, 22, Y0, 26, "south", double=True)
        path(d, 22, 25, 23, 25, border=False)
        long_table(d, 17, 30, 27, Y0, "oak")
        long_table(d, 17, 33, 27, Y0, "oak")
        d.fill(15, Y0, 27, 29, Y0, 27, "oak_planks") if False else None
        for x in range(16, 29):
            put(d, x, Y0, 27, slab("oak_slab", "top")) if x in (20, 21, 22, 23, 24) else None
        wall_art(d, (15, 27, 29, 35), Y0, colors=("yellow", "red"))
        lights(d, (15, 27, 29, 35), Y0, 6)
        d.sign(22, 6, 37, "south", ["SCHOOL", "HALL"], "oak")
    if L >= 5:
        sr2 = bldg(d, 2, 22, 12, 36, 2, "gable", "z", mat="yellow_terracotta", up="yellow_terracotta")
        ext_door(d, 7, Y0, 22, "south")
        stair_up(d, 11, 24, Y0, 7, "south")
        classroom(d, (3, 23, 10, 35), Y0, board="s")
        classroom(d, (3, 23, 11, 35), 7, board="s")
        d.sign(7, 5, 21, "north", ["JUNIOR", "SCHOOL"], "oak")
        kt = bldg(d, 30, 32, 40, 40, 2, "gable", "z", mat="bricks", up="yellow_terracotta")
        link(d, 30, Y0, 34, "east")
        kitchen(d, (31, 33, 39, 39), Y0)
        table_set(d, (31, 35, 39, 39), Y0, "study", sit=False)
        stair_up(d, 39, 34, Y0, 7, "south")
        dorm(d, (31, 33, 37, 38), 7, 2, head="w", color="yellow", desks=False)
        chimney(d, 40, 36, Y0, 17)
        # playing field and school garden
        lawn(d, 2, 40, 28, 48)
        for z in range(41, 48):
            for x in (3, 27):
                if z in (43, 46):
                    for y in (2, 3, 4):
                        put(d, x, y, z, "white_concrete" if y < 4 else "white_concrete")
        for x in range(3, 28):
            put(d, x, 1, 44, "white_concrete") if x == 15 else None
        for x in range(42, 48):
            for z in range(34, 47):
                if x in (42, 47) or z in (34, 46):
                    put(d, x, 2, z, "oak_fence")
                else:
                    d.set(x, 1, z, "farmland[moisture=7]")
                    d.set(x, 2, z, ("carrots[age=7]", "potatoes[age=7]", "beetroots[age=3]", "wheat[age=7]")[z % 4])
        put(d, 44, 2, 33, "composter[level=4]")
    return d


def sch_neoterra(rel, L):
    d = new("Neoterra", rel, (53, 30, 51), paving="smooth_stone")
    fins = ("yellow_concrete", "lime_concrete", "orange_concrete")
    pnf = 2 if L >= 3 else 1
    p = bldg(d, 6, 6, 20, 16, pnf, "flat", glassy=True, win="nsw")
    for x in range(7, 20, 3):
        for y in range(Y0, 5 * pnf + 2):
            d.set(x, y, 5, fins[x % 3])
    ext_door(d, 12, Y0, 6, "south", double=True)
    d.sign(12, 6, 4, "north", ["SUNRISE", "SCHOOL"], "birch", glow=True, color="yellow")
    d.hut(7, Y0, 7)
    keep(d, 8, Y0, 7)
    classroom(d, (7, 7, 19, 15), Y0, board="s", need=d.req["seats"], teacher_spot=True)
    shelf_runs(d, [(7, 9, 7, 13, Y0, 1), (7, 9, 7, 13, Y0 + 1, 1)], d.req["bookshelves"])
    for x in (4, 22):
        post_lamp(d, x, 4)
    for x in range(8, 19, 4):
        put(d, x, 2, 3, "moss_block")
        put(d, x, 3, 3, "flowering_azalea")
    if pnf > 1:
        stair_up(d, 19, 8, Y0, 7, "south")
        classroom(d, (7, 7, 18, 15), 7, board="n")
        roof_garden(d, p, "solar")
    if L >= 2:
        c2 = bldg(d, 24, 6, 36, 16, 1, "flat", glassy=True, win="nse")
        for x in range(25, 36, 3):
            for y in range(Y0, 7):
                d.set(x, y, 5, fins[(x + 1) % 3])
        ext_door(d, 30, Y0, 6, "south")
        d.box(20, Y0, 9, 24, 5, 13, "glass", floor="polished_diorite")
        d.fill(20, 6, 9, 24, 6, 13, "smooth_quartz")
        d.clear(21, Y0, 10, 23, 5, 12)
        arch(d, 20, Y0, 11, "east")
        arch(d, 24, Y0, 11, "east")
        if L >= 3:
            art_room(d, (25, 7, 35, 15), Y0)
            d.sign(30, 6, 4, "north", ["ART STUDIO"], "birch", glow=True, color="lime")
        else:
            classroom(d, (25, 7, 35, 15), Y0, board="e")
        roof_garden(d, c2, "garden")
    if L >= 4:
        gy = bldg(d, 6, 20, 34, 32, 1, "flat", wh=8, win="n", mat="light_gray_concrete")
        link(d, 12, Y0, 16, "south") if False else ext_door(d, 20, Y0, 20, "north", double=True)
        for x in range(7, 34):
            for z in range(21, 32):
                d.set(x, 1, z, "white_concrete" if x in (7, 33, 20) or z in (21, 31) else "orange_terracotta")
        for x in (8, 32):
            d.set(x, 4, 26, "white_stained_glass")
            d.set(x, 5, 26, "white_stained_glass")
            put(d, x + (1 if x == 8 else -1), 4, 26, "iron_bars")
        for z in range(22, 31, 2):
            put(d, 7, Y0, z, "light_blue_wool")
        for x in range(10, 31, 4):
            for z in (23, 29):
                d.set(x, 9, z, "sea_lantern")
        d.sign(20, 7, 19, "north", ["SPORTS", "HALL"], "birch", glow=True, color="yellow")
    if L >= 3:
        playground(d, 38, 28, 50, 44)
        for x in range(38, 51):
            put(d, x, 6, 27, slab("smooth_quartz_slab", "top"))
    if L >= 5:
        sc = bldg(d, 38, 6, 50, 24, 3, "flat", glassy=True, win="nsew")
        ext_door(d, 44, Y0, 6, "south", double=True)
        stair_up(d, 39, 8, Y0, 7, "south")
        stair_up(d, 49, 22, 7, 12, "north")
        lab(d, (39, 7, 49, 15), Y0)
        table_set(d, (39, 16, 49, 23), Y0, "dining")
        shelf_wall(d, (39, 7, 49, 23), "e", 7, 3)
        table_set(d, (39, 8, 48, 23), 7, "study", sit=False)
        classroom(d, (39, 7, 49, 23), 12, board="s")
        roof_garden(d, sc, "garden")
        d.sign(44, 6, 4, "north", ["SCIENCE", "& LIBRARY"], "birch", glow=True, color="orange")
        cn = bldg(d, 6, 36, 30, 46, 1, "flat", glassy=True, win="nsw")
        ext_door(d, 18, Y0, 36, "north", double=True)
        kitchen(d, (7, 37, 29, 39), Y0)
        table_set(d, (7, 40, 29, 45), Y0, "dining")
        roof_garden(d, cn, "solar")
        for x in range(32, 38):
            for z in range(36, 47, 3):
                plant_tree(d, x, z) if x == 34 else None
    return d


def sch_cascadia(rel, L):
    d = new("Cascadia", rel, (53, 28, 51), paving="coarse_dirt")
    X1, X2, Z1, Z2 = 18, 28, 8, 20
    b = bldg(d, X1, Z1, X2, Z2, 1, "gable", "z", wh=5)
    mid = 23
    ridge = b["ridge"]
    for x in range(mid - 1, mid + 2):
        for z in range(Z1, Z1 + 3):
            d.set(x, ridge, z, "birch_planks")
    for x, z in ((mid - 1, Z1), (mid + 1, Z1), (mid - 1, Z1 + 2), (mid + 1, Z1 + 2)):
        for y in range(ridge + 1, ridge + 3):
            d.set(x, y, z, "birch_fence")
    d.hip(mid - 1, Z1, mid + 1, Z1 + 2, ridge + 3, "spruce_stairs", "spruce_slab", overhang=1)
    d.set(mid, ridge + 3, Z1 + 1, "spruce_planks")
    bell(d, mid, ridge + 2, Z1 + 1)
    ext_door(d, mid, Y0, Z1, "south")
    d.fill(X1, 1, Z1 - 3, X2, 1, Z1 - 1, "spruce_planks")
    for x in (X1, X2):
        for y in range(Y0, 6):
            put(d, x, y, Z1 - 3, log("stripped_birch_log"))
    for x in range(X1 - 1, X2 + 2):
        d.set(x, 7, Z1 - 4, st("spruce_stairs", "south"))
        for z in range(Z1 - 3, Z1):
            d.set(x, 7, z, slab("spruce_slab"))
    d.sign(mid, 6, Z1 - 1, "north", ["SCHOOL", "DIST. No. 7"], "spruce")
    d.hut(X1 + 1, Y0, Z1 + 1)
    keep(d, X1 + 2, Y0, Z1 + 1)
    classroom(d, (X1 + 1, Z1 + 1, X2 - 1, Z2 - 1), Y0, board="s", need=d.req["seats"], teacher_spot=True, h=5)
    shelf_runs(d, [(X1 + 1, Z2 - 4, X1 + 1, Z2 - 2, Y0, 1), (X1 + 1, Z2 - 4, X1 + 1, Z2 - 2, Y0 + 1, 1),
                   (X1 + 1, Z2 - 4, X1 + 1, Z2 - 2, Y0 + 2, 1)], d.req["bookshelves"])
    for z in (Z1 + 1, Z1 + 2):
        put(d, X2 - 1, Y0 + 1, z, "spruce_fence")
    chimney(d, mid, Z2 + 1, Y0, ridge)
    for x in (X1 - 2, X2 + 2):
        post_lamp(d, x, Z1 - 2)
    if L >= 2:
        tc = bldg(d, 4, 8, 14, 16, 1, "gable", "z", mat="stripped_spruce_log", up="stripped_spruce_log")
        ext_door(d, 9, Y0, 8, "south")
        lounge(d, (5, 9, 13, 12), Y0)
        dorm(d, (5, 13, 13, 15), Y0, 1, head="s", color="red")
        chimney(d, 4, 12, Y0, 13)
        for x in range(3, 16):
            put(d, x, 2, 5, "spruce_fence") if x != 9 else None
        flowerbed(d, 4, 6, 7, 7, ("fern", "blue_orchid", "allium", "dandelion"))
        d.sign(9, 5, 7, "north", ["TEACHER"], "spruce")
    if L >= 3:
        lt = bldg(d, X2, 11, 33, 18, 1, "gable", "z", mat="mangrove_planks", up="mangrove_planks", win="e")
        link(d, X2, Y0, 14, "east")
        art_room(d, (X2 + 1, 12, 32, 17), Y0)
        c2 = bldg(d, 36, 8, 46, 20, 1, "gable", "z", wh=5)
        ext_door(d, 41, Y0, 8, "south")
        classroom(d, (37, 9, 45, 19), Y0, board="s", h=5)
        d.sign(41, 6, 7, "north", ["UPPER", "GRADES"], "spruce")
        chimney(d, 41, 21, Y0, c2["ridge"])
    if L >= 4:
        gm = bldg(d, 10, 26, 40, 36, 1, "gable", "x", wh=7, mat="mangrove_planks", up="mangrove_planks")
        ext_door(d, 25, Y0, 26, "south", double=True)
        path(d, 25, 21, 26, 25, "spruce_planks", border=False)
        for x in range(11, 40):
            for z in range(27, 36):
                d.set(x, 1, z, "birch_planks" if (x + z) % 2 else "spruce_planks")
        for x in (12, 38):
            d.set(x, 5, 31, "white_stained_glass")
            put(d, x + (1 if x == 12 else -1), 5, 31, "iron_bars")
        for z in range(28, 35, 3):
            bench(d, 15, z, 19, z, Y0, "west", "spruce", tag=None) if False else None
        lights(d, (11, 27, 39, 35), Y0, 7)
        d.sign(25, 7, 25, "north", ["GYMNASIUM"], "spruce")
        playground(d, 2, 22, 8, 40)
    if L >= 5:
        lr = bldg(d, 40, 26, 52, 38, 2, "gable", "z", mat="stripped_spruce_log", up="stripped_spruce_log")
        ext_door(d, 46, Y0, 26, "south")
        kitchen(d, (41, 27, 51, 30), Y0)
        table_set(d, (41, 31, 51, 37), Y0, "dining")
        stair_up(d, 51, 31, Y0, 7, "south")
        classroom(d, (41, 27, 50, 37), 7, board="w")
        chimney(d, 52, 32, Y0, 17)
        d.sign(46, 5, 25, "north", ["LUNCH", "ROOM"], "spruce")
        for x in range(12, 40):
            for z in range(40, 49):
                if x in (12, 39) or z in (40, 48):
                    put(d, x, 2, z, "spruce_fence")
                elif z % 2:
                    d.set(x, 1, z, "farmland[moisture=7]")
                    d.set(x, 2, z, ("carrots[age=7]", "potatoes[age=7]", "wheat[age=7]")[x % 3])
        ws = bldg(d, 44, 42, 52, 48, 1, "gable", "x", mat="stripped_spruce_log", win="")
        ext_door(d, 48, Y0, 42, "south", double=True)
        workshop(d, (45, 43, 51, 47), Y0)
        bn = bldg(d, 2, 42, 10, 50, 1, "gable", "z", mat="mangrove_planks", up="mangrove_planks", wh=5)
        ext_door(d, 6, Y0, 42, "south", double=True)
        for z in range(44, 50, 2):
            put(d, 3, Y0, z, "hay_block[axis=y]")
            put(d, 9, Y0, z, "hay_block[axis=y]")
        cart(d, 6, 46, "z")
        d.sign(6, 5, 41, "north", ["WAGON", "SHED"], "spruce")
        for y in range(Y0, 14):
            d.set(16, y, 4, "spruce_fence")
        d.set(16, 14, 4, "red_wool")
        d.set(16, 13, 4, "white_wool")
    return d


@design("school")
def school_v2(pack, rel, L):
    return common_materials({"Hearthwood": sch_hearthwood, "Cascadia": sch_cascadia, "Neoterra": sch_neoterra}[pack](rel, L))


# ============================================================================================ COMMUNITY COLLEGE v2
def outdoor_class(d, cx, cz, back="north", kind="plinth"):
    """Outdoor teaching spot: speaker's plinth/stump (stand_out) facing two rows of benches (sit_out)."""
    if kind == "plinth":
        d.set(cx, 1, cz, "polished_andesite" if d.pack != "Cascadia" else "cobblestone")
        d.set(cx, Y0, cz, slab("stone_brick_slab" if d.pack == "Hearthwood" else "smooth_quartz_slab" if d.pack == "Neoterra" else "spruce_slab"))
        d.tag(cx, Y0, cz, "stand_out")
        d.placed["spots"]["stand_out"] = d.placed["spots"].get("stand_out", 0) + 1
        keep(d, cx, Y0 + 1, cz, 2)
    else:
        d.set(cx, 1, cz, log("stripped_spruce_log"))
        d.spot(cx, Y0, cz, "stand_out")
        keep(d, cx, Y0, cz)
    wood = d.S["wood"]
    dz = 3 if back == "north" else -3
    for row in (0, 2):
        for x in range(cx - 2, cx + 3):
            z = cz - dz - (row if dz > 0 else -row)
            if d.air(x, Y0, z):
                sit_out(d, x, Y0, z, back, wood)


def col_hearthwood(rel, L):
    d = new("Hearthwood", rel, (49, 30, 49))
    mnf = 2 if L >= 3 else 1
    m = bldg(d, 16, 12, 30, 22, mnf, "gable", "z")
    ext_door(d, 23, Y0, 12, "south")
    for x in (21, 25):
        for y in range(Y0, 6):
            put(d, x, y, 10, "quartz_pillar[axis=y]")
    d.fill(21, 6, 10, 25, 6, 11, "smooth_stone")
    d.fill(21, 1, 9, 25, 1, 11, "polished_andesite")
    d.sign(23, mnf * 5 + 4, 11, "north", ["MECHANICS'", "INSTITUTE"], "dark_oak") if False else \
        d.sign(23, 5, 11, "north", ["MECHANICS'", "INSTITUTE"], "dark_oak")
    d.hut(17, Y0, 13)
    keep(d, 18, Y0, 13)
    d.item(23, Y0, 20, "lectern", "north")
    keep(d, 23, Y0, 19)
    blackboard(d, 21, 21, 25, 21, Y0 + 1, "north")
    for z in (15, 17):
        for x in list(range(18, 22)) + list(range(24, 28)):
            if d.placed["seats"] < d.req["seats"]:
                d.chair(x, Y0, z, "north", "dark_oak")
    runs = [(17, 15, 17, 21, Y0, 2), (29, 14, 29, 21, Y0, 2), (17, 15, 17, 21, Y0 + 2, 1), (29, 14, 29, 21, Y0 + 2, 1)]
    corners(d, (17, 13, 29, 21), Y0)
    wall_art(d, (17, 13, 29, 21), Y0, "ew", ("blue", "white"))
    # walled front garden with the speaker's plinth and benches
    lawn(d, 4, 1, 44, 8)
    path(d, 22, 0, 24, 9)
    for x in range(3, 46):
        if x not in (22, 23, 24):
            put(d, x, 2, 0, "brick_wall")
    outdoor_class(d, 10, 3, "south")
    for x in (14, 32):
        post_lamp(d, x, 6)
    flowerbed(d, 28, 3, 40, 4)
    plant_tree(d, 36, 7)
    if L >= 2:
        rr = bldg(d, 30, 13, 38, 21, 2 if L >= 3 else 1, "gable", "x", mat="bricks", up="bricks")
        link(d, 30, Y0, 17, "east")
        runs += [(31, 14, 37, 14, Y0, 2), (31, 20, 37, 20, Y0, 2)]
        long_table(d, 32, 18, 35, Y0, "dark_oak", sit=False)
        if L >= 3:
            link(d, 30, 7, 17, "east")
            table_set(d, (31, 14, 37, 20), 7, "study", sit=False)
            for x in (40, 44):
                post_lamp(d, x, 10)
            flowerbed(d, 39, 12, 44, 14)
            for x in range(39, 46):
                put(d, x, 2, 11, "dark_oak_fence")
            flowerbed(d, 4, 10, 15, 11)
            for x in (5, 15):
                post_lamp(d, x, 9)
            runs += [(31, 14, 37, 14, 7, 3), (31, 20, 37, 20, 7, 3)]
        d.sign(34, 5, 12, "north", ["READING", "ROOM"], "dark_oak")
        if need(d, "lectern") > 1:
            d.item(37, Y0, 16, "lectern", "west")
            keep(d, 36, Y0, 16)
    if L >= 2:
        tw = bldg(d, 4, 13, 16, 23, 2 if L >= 5 else 1, "gable", "x", mat="bricks", up="bricks")
        if L >= 5:
            stair_up(d, 5, 22, Y0, 7, "east") if False else None
            link(d, 16, 7, 17, "west")
            classroom(d, (5, 14, 15, 22), 7, board="w")
        link(d, 16, Y0, 17, "west")
        workshop(d, (5, 14, 15, 22), Y0)
        chimney(d, 4, 18, Y0, tw["ridge"] + 1)
        d.sign(10, 5, 12, "north", ["TECHNICAL", "SCHOOL"], "dark_oak")
    if mnf > 1:
        stair_up(d, 19, 14, Y0, 7, "east")
        runs += [(17, 13, 17, 21, 7, 3), (18, 21, 27, 21, 7, 3), (17, 13, 27, 13, 7, 3)]
        table_set(d, (18, 14, 28, 20), 7, "study", sit=False)
        clockface(d, 23, 14, 12, "north", "white_concrete") if False else None
    if L >= 4:
        th = bldg(d, 14, 26, 36, 38, 1, "gable", "x", wh=7)
        ext_door(d, 25, Y0, 26, "south", double=True)
        path(d, 25, 23, 26, 25, border=False)
        lecture(d, (15, 27, 35, 37), Y0, "s", h=7)
        for x in range(18, 33):
            put(d, x, Y0, 36, "red_carpet")
        d.sign(25, 6, 25, "north", ["THEATRE"], "dark_oak")
    if L >= 5:
        hs = bldg(d, 2, 26, 12, 40, 2, "gable", "z", mat="white_terracotta", up="white_terracotta")
        ext_door(d, 7, Y0, 26, "south")
        stair_up(d, 11, 28, Y0, 7, "south")
        lounge(d, (3, 27, 10, 32), Y0)
        table_set(d, (3, 33, 11, 39), Y0, "dining")
        dorm(d, (3, 27, 11, 39), 7, 6, head="w", color="blue")
        chimney(d, 2, 33, Y0, 16)
        d.sign(7, 5, 25, "north", ["HOSTEL"], "dark_oak")
        ct = bldg(d, 38, 28, 46, 38, 2, "gable", "z", mat="calcite", up="calcite")
        ext_door(d, 42, Y0, 28, "south")
        stair_up(d, 45, 30, Y0, 7, "south")
        lounge(d, (39, 29, 44, 33), Y0)
        kitchen(d, (39, 34, 45, 37), Y0)
        dorm(d, (39, 29, 44, 37), 7, 2, head="w")
        chimney(d, 46, 33, Y0, 16)
        lawn(d, 2, 40, 46, 48)
        for x in range(4, 46, 6):
            plant_tree(d, x, 44)
            flowerbed(d, x + 2, 41, x + 4, 42)
    shelf_runs(d, runs, d.req["bookshelves"])
    return d


def col_neoterra(rel, L):
    d = new("Neoterra", rel, (51, 30, 51), paving="smooth_stone")
    Q = "smooth_quartz"
    nf = 2 if L >= 3 else 1
    p = bldg(d, 14, 16, 30, 26, nf, "flat", glassy=True, win="nsw")
    ext_door(d, 22, Y0, 16, "south", double=True)
    d.sign(22, 6, 15, "north", ["LEARNING", "PAVILION"], "birch", glow=True, color="orange")
    d.hut(15, Y0, 17)
    keep(d, 16, Y0, 17)
    d.item(28, Y0, 21, "lectern", "west")
    keep(d, 27, Y0, 21)
    for z in range(19, 24):
        d.set(29, 4, z, "black_concrete")
        d.set(29, 5, z, "black_concrete")
    for x in (19, 21, 23, 25):
        for z in (19, 20, 22, 23):
            if d.placed["seats"] < d.req["seats"]:
                d.chair(x, Y0, z, "west", "birch")
    runs = [(15, 25, 22, 25, Y0, 2), (15, 19, 15, 24, Y0, 2), (23, 25, 29, 25, Y0, 2), (15, 25, 29, 25, Y0 + 2, 1)]
    corners(d, (15, 17, 29, 25), Y0, ["potted_bamboo"])
    # amphitheatre: stage by the pavilion, tiers rising to the street
    for x in range(16, 29):
        for z in (13, 14):
            d.set(x, 1, z, "polished_andesite")
    d.spot(22, Y0, 14, "stand_out")
    keep(d, 22, Y0, 14)
    if need(d, "lectern") > 1:
        d.item(24, Y0, 14, "lectern", "north")
        keep(d, 24, Y0, 13)
    for k, z in enumerate((11, 9, 7)):
        for zz in (z, z - 1):
            for x in range(15, 30):
                for y in range(Y0, Y0 + k):
                    d.set(x, y, zz, Q)
        for x in range(16, 29):
            if x != 22:
                sit_out(d, x, Y0 + k, z, "north", "birch")
    for x in (14, 30):
        post_lamp(d, x, 13)
    if L >= 2:
        mk = bldg(d, 30, 16, 40, 26, nf, "flat", glassy=False, win="ns", mat="orange_terracotta", up="mangrove_planks")
        link(d, 30, Y0, 21, "east")
        workshop(d, (31, 17, 39, 25), Y0)
        d.sign(35, 6, 15, "north", ["MAKER", "SPACE"], "birch", glow=True, color="orange")
        roof_garden(d, mk, "solar")
        for x in (32, 35, 38):                                       # planters along the maker space front
            put(d, x, 2, 14, "moss_block")
            put(d, x, 3, 14, "flowering_azalea")
    if nf > 1:
        stair_up(d, 16, 19, Y0, 7, "south")
        table_set(d, (16, 17, 29, 25), 7, "study", sit=False)
        runs += [(17, 25, 29, 25, 7, 3)]
        roof_garden(d, p, "garden")
        if L >= 2:
            link(d, 30, 7, 21, "east")
            classroom(d, (31, 17, 39, 25), 7, board="e")
    if L >= 3:
        for k, z in enumerate((5,)):
            for x in range(15, 30):
                for y in range(Y0, Y0 + 3):
                    d.set(x, y, z, Q) if False else None
        for x in range(14, 31):                                      # shade canopy over the stage
            d.set(x, 7, 12, slab("smooth_quartz_slab", "top"))
            d.set(x, 7, 13, slab("smooth_quartz_slab", "top"))
        for x in (14, 30):
            for y in range(Y0, 7):
                d.set(x, y, 12, "white_concrete")
    if L >= 4:
        lb = bldg(d, 2, 16, 14, 32, 3, "flat", glassy=True, win="nsw", mat="white_concrete", up="mangrove_planks")
        link(d, 14, Y0, 21, "west")
        stair_up(d, 3, 30, Y0, 7, "north")
        stair_up(d, 13, 18, 7, 12, "south")
        for y in (Y0, 7, 12):
            for z in range(20, 31, 3):
                stall_row(d, 4, 11, z, y, 2)
            lights(d, (3, 17, 13, 31), y)
        runs += [(3, 17, 12, 17, Y0, 3)]
        roof_garden(d, lb, "garden")
        d.sign(8, 6, 15, "north", ["LIBRARY"], "birch", glow=True, color="orange")
    if L >= 5:
        st_ = bldg(d, 36, 30, 46, 40, 5, "flat", glassy=True, win="nsew", mat="white_concrete", up="mangrove_planks")
        ext_door(d, 41, Y0, 30, "south", double=True)
        for k in range(4):
            stair_up(d, 37 if k % 2 == 0 else 45, 31 if k % 2 == 0 else 39, Y0 + 5 * k, Y0 + 5 * k + 5,
                     "south" if k % 2 == 0 else "north")
        lounge(d, (38, 32, 44, 38), Y0)
        for k in range(1, 5):
            (art_room if k % 2 else classroom)(d, (38, 32, 44, 38), Y0 + 5 * k)
        roof_garden(d, st_, "solar")
        cf = bldg(d, 16, 30, 30, 38, 1, "flat", glassy=True, win="nsw")
        ext_door(d, 23, Y0, 30, "south", double=True)
        kitchen(d, (17, 31, 29, 33), Y0)
        table_set(d, (17, 34, 29, 37), Y0, "dining")
        roof_garden(d, cf, "garden")
        lawn(d, 2, 42, 48, 49)
        for x in range(4, 48, 6):
            plant_tree(d, x, 45)
            park_bench(d, x + 2, 47, "x", "south")
    shelf_runs(d, runs, d.req["bookshelves"])
    return d


def col_cascadia(rel, L):
    d = new("Cascadia", rel, (53, 28, 51), paving="coarse_dirt")
    mnf = 2 if L >= 3 else 1
    h = bldg(d, 12, 16, 30, 26, mnf, "gable", "x")
    ext_door(d, 21, Y0, 16, "south")
    d.fill(12, 1, 13, 30, 1, 15, "spruce_planks")
    for x in (12, 18, 24, 30):
        for y in range(Y0, 6):
            put(d, x, y, 13, log("spruce_log"))
    for x in range(11, 32):
        d.set(x, 6, 12, st("spruce_stairs", "south"))
        for z in range(13, 16):
            d.set(x, 6, z, slab("spruce_slab"))
    d.sign(21, 5, 15, "north", ["VALLEY", "COLLEGE"], "spruce")
    for x in (15, 27):
        put(d, x, 5, 14, "lantern[hanging=true,waterlogged=false]")
    d.hut(13, Y0, 17)
    keep(d, 14, Y0, 17)
    d.item(28, Y0, 21, "lectern", "west")
    keep(d, 27, Y0, 21)
    blackboard(d, 29, 19, 29, 23, Y0 + 1, "west", "black_concrete", "spruce")
    for x in (18, 20, 22, 24):
        for z in (18, 19, 20, 22, 23, 24):
            if d.placed["seats"] < d.req["seats"]:
                d.chair(x, Y0, z, "west", "spruce")
    d.hearth(13, Y0, 22, "east", 7, "cobblestone", "campfire")
    chimney(d, 11, 22, Y0, h["ridge"] + 1)
    runs = [(13, 25, 17, 25, Y0, 2), (23, 25, 28, 25, Y0, 2), (13, 25, 28, 25, Y0 + 2, 1), (13, 17, 13, 20, Y0 + 1, 1)]
    # fire circle with log benches and the speaker's stump
    cx, cz = 21, 6
    for x in range(cx - 4, cx + 5):
        for z in range(cz - 4, cz + 5):
            if abs(x - cx) + abs(z - cz) <= 5:
                d.set(x, 1, z, "gravel" if abs(x - cx) + abs(z - cz) <= 2 else "coarse_dirt")
    d.set(cx, Y0, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for x in (cx - 1, cx, cx + 1):
        sit_out(d, x, Y0, cz - 3, "north", "spruce")
    for z in (cz - 1, cz, cz + 1):
        sit_out(d, cx - 3, Y0, z, "west", "spruce")
        sit_out(d, cx + 3, Y0, z, "east", "spruce")
    d.set(cx, 1, cz + 3, log("stripped_spruce_log"))
    d.spot(cx, Y0, cz + 3, "stand_out")
    keep(d, cx, Y0, cz + 3)
    if need(d, "lectern") > 1:
        d.item(cx + 1, Y0, cz + 3, "lectern", "north")
        keep(d, cx + 1, Y0, cz + 4)
    for x, z in ((cx - 5, cz - 3), (cx + 5, cz - 3)):
        post_lamp(d, x, z)
    if L >= 2:
        sh = bldg(d, 30, 17, 38, 25, 1, "gable", "z", mat="stripped_spruce_log", up="stripped_spruce_log")
        link(d, 30, Y0, 21, "east")
        workshop(d, (31, 18, 37, 24), Y0)
        d.sign(34, 5, 16, "north", ["SHOP"], "spruce")
        for z in range(18, 25, 2):
            put(d, 39, 2, z, log("spruce_log", "z"))
            put(d, 39, 3, z, log("spruce_log", "z"))
    if L >= 2:
        rl = bldg(d, 2, 16, 12, 26, 2 if L >= 3 else 1, "gable", "z", mat="stripped_dark_oak_log", up="stripped_dark_oak_log")
        if L >= 3:
            stair_up(d, 11, 25, Y0, 7, "north") if False else stair_up(d, 4, 25, Y0, 7, "east")
            table_set(d, (3, 17, 11, 25), 7, "study", sit=False)
            runs += [(3, 17, 11, 17, 7, 2)]
        ext_door(d, 7, Y0, 16, "south")
        for z in range(18, 26, 2):
            stall_row(d, 3, 6, z, Y0, 2)
        for z in (18, 21, 24):
            desk(d, 10, Y0, z, "west")
        runs += [(3, 17, 6, 17, Y0, 2)]
        chimney(d, 2, 21, Y0, 13)
    if mnf > 1:
        stair_up(d, 15, 25, Y0, 7, "east")
        runs += [(13, 17, 29, 17, 7, 3), (13, 17, 13, 25, 7, 3), (29, 17, 29, 25, 7, 3)]
        table_set(d, (14, 18, 28, 24), 7, "study", sit=False)
    if L >= 4:
        bk = bldg(d, 36, 30, 50, 40, 2, "gable", "x", mat="mangrove_planks", up="mangrove_planks")
        ext_door(d, 43, Y0, 30, "south")
        stair_up(d, 49, 32, Y0, 7, "south")
        kitchen(d, (37, 31, 48, 33), Y0)
        table_set(d, (37, 34, 48, 39), Y0, "dining")
        dorm(d, (37, 31, 48, 39), 7, 8, head="n")
        chimney(d, 50, 35, Y0, 16)
        d.sign(43, 5, 29, "north", ["BUNKHOUSE"], "spruce")
        for x in range(36, 51):                                      # bunkhouse porch
            for z in (27, 28, 29):
                d.set(x, 1, z, "spruce_planks")
            if x % 4 == 0:
                for y in range(Y0, 5):
                    put(d, x, y, 27, log("spruce_log"))
            for z in (27, 28, 29):
                put(d, x, 5, z, slab("spruce_slab"))
        for x in range(36, 51):                                      # porch rail and woodpile
            if x % 4 and x not in (43,):
                put(d, x, Y0, 26, "spruce_fence")
        for x in range(30, 35):
            for y in (Y0, Y0 + 1):
                put(d, x, y, 41, log("spruce_log", "x"))
        for z in range(31, 40):                                      # rail fence beside the bunkhouse
            put(d, 35, Y0, z, "spruce_fence")
        for x in range(37, 50, 4):                                   # lanterns on the bunkhouse back wall
            put(d, x, 4, 41, "wall_torch[facing=south]") if False else put(d, x, 5, 41, "lantern[hanging=true,waterlogged=false]") if False else None
        for z in (32, 36):
            put(d, 34, Y0, z, "spruce_fence")
            put(d, 34, Y0 + 1, z, "lantern[hanging=false,waterlogged=false]")
        for x in (37, 41, 45, 49):
            d.chair(x, Y0, 28, "south", "spruce", sit=False)
            put(d, x + 1, Y0, 28, "barrel[facing=up,open=false]") if False else put(d, x + 1, 4, 28, "lantern[hanging=true,waterlogged=false]")
    if L >= 5:
        sm = bldg(d, 36, 42, 50, 50, 2, "gable", "x", mat="stripped_spruce_log")
        stair_up(d, 49, 44, Y0, 7, "south")
        table_set(d, (37, 43, 48, 49), 7, "study", sit=False)
        lights(d, (37, 43, 49, 49), 7)
        ext_door(d, 43, Y0, 42, "south", double=True)
        workshop(d, (37, 43, 49, 49), Y0)
        for x in range(37, 50, 2):
            put(d, x, Y0, 49, log("spruce_log", "x"))
        d.sign(43, 5, 41, "north", ["SAWMILL", "CLASS"], "spruce")
        for x in range(37, 50, 3):
            put(d, x, Y0, 51, log("spruce_log", "x")) if d.bp.inside(x, Y0, 51) else None
        for x in (35, 51):
            post_lamp(d, x, 44)
        gh = (4, 32, 16, 42)
        for x in range(gh[0], gh[2] + 1):
            for z in range(gh[1], gh[3] + 1):
                edge = x in (gh[0], gh[2]) or z in (gh[1], gh[3])
                if edge:
                    for y in range(Y0, 5):
                        d.set(x, y, z, "glass" if (x + z) % 3 else log("spruce_log"))
                else:
                    d.set(x, 1, z, "farmland[moisture=7]" if (x + z) % 2 else "spruce_planks")
                    if (x + z) % 2:
                        d.set(x, Y0, z, ("fern", "sweet_berry_bush[age=2]", "carrots[age=7]")[x % 3])
                d.set(x, 5, z, "glass")
        d.set(10, Y0, 32, AIR)
        d.set(10, Y0 + 1, 32, AIR)
        d.door(10, Y0, 32, "south", "spruce")
        bn = bldg(d, 20, 32, 32, 44, 1, "gable", "z", mat="mangrove_planks", up="mangrove_planks", wh=6)
        ext_door(d, 26, Y0, 32, "south", double=True)
        for z in range(34, 44, 3):
            put(d, 21, Y0, z, "hay_block[axis=y]")
            put(d, 31, Y0, z, "hay_block[axis=y]")
        cart(d, 26, 38, "z")
        store(d, (21, 33, 31, 43), Y0, aisle="z") if False else None
        d.sign(26, 6, 31, "north", ["AG BARN"], "spruce")
    shelf_runs(d, runs, d.req["bookshelves"])
    return d


@design("communitycollege")
def communitycollege_v2(pack, rel, L):
    return common_materials({"Hearthwood": col_hearthwood, "Cascadia": col_cascadia, "Neoterra": col_neoterra}[pack](rel, L))
