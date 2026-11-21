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


def dispensary(d, x, z, along, y, face, L):
    """Brewing stand, furnace (steriliser), wash basin, supply rack (L2+), barrels (L3+) in a row."""
    items = ["brewing_stand", "furnace", "water_cauldron"]
    if d.req["racks"]:
        items.append("rack")
    items += ["barrel"] * need(d, "barrel")
    line_items(d, x, z, along, y, face, items)


def beds_left(d):
    return d.req["beds"] - d.placed["beds"]


def stall_row(d, x1, x2, z, y, h, face_desk=None):
    """Oxford-style press: a double-sided bookcase run along x with reading desks at its ends."""
    for x in range(x1, x2 + 1):
        for k in range(h):
            if d.air(x, y + k, z) and (x, y + k, z) not in d.res:
                d.bookshelf(x, y + k, z)


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
