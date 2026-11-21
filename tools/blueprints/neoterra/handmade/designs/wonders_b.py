"""
Grand projects, group B: the Grand Bridge and the Royal Granary (each with two wing child huts).

Grand bridge (river runs north-south through the plot, the bridge carries the road west-east; wings at both ends)
  Hearthwood  "King's Bridge": humpbacked medieval stone bridge of three arches on cutwater piers, stepped
              approaches, a refuge bay over the middle (later a little chantry shrine). Wings = stone gate towers the
              road passes through (portcullis, crenellations, at L5 a slate spire).
  Cascadia    "Cascadia Crossing": timber trestle bridge that becomes a covered bridge (L1 log stringers on
              trestle bents, L2 open trusses, L3 roof and board siding, L4 daylight windows + side gallery, L5 portal
              false fronts). Wings = log blockhouse gate towers with an overhanging upper storey and a lookout.
  Neoterra    "Skyline Span": white suspension bridge. Slim deck with glass railings and a belvedere; the wings are
              the H-shaped pylons the road passes through, the main cables sag between them with chain hangers.
              L1 is a beam bridge on two V piers, each level raises the pylons and the cable.

Royal granary
  Hearthwood  great tithe barn: long buttressed stone barn with a steep tiled roof and a wagon porch, forecourt with
              the two round stone dovecotes (wings) at the front corners.
  Cascadia    prairie-style timber grain elevator with a headhouse, a drive-through wagon shed and a rail siding;
              wings = round stave silos linked by conveyor galleries at the top levels.
  Neoterra    seed vault: a concrete wedge portal jutting out of a grassed mound with a glowing art band, research
              pavilion; wings = white concrete silos with cyan bands.

Wings are pasted without rotation at both ends, so they are drawn symmetric about their own centre line.
"""
from hm import Design, design, AIR

WATER = "water[level=0]"
ROOT = "wonders/"


# ----------------------------------------------------------------------------------------------- helpers
def stair(b, facing, half="bottom", shape="straight"):
    return f"{b}[facing={facing},half={half},shape={shape},waterlogged=false]"


def slab(b, t="bottom"):
    return f"{b}[type={t},waterlogged=false]"


def lantern(hanging=False):
    return f"lantern[hanging={'true' if hanging else 'false'},waterlogged=false]"


def disc(r, cx, cz):
    """Cells of a filled circle of radius r around (cx, cz) (cx/cz may be .5)."""
    out = set()
    for x in range(int(cx - r - 1), int(cx + r + 2)):
        for z in range(int(cz - r - 1), int(cz + r + 2)):
            if (x - cx) ** 2 + (z - cz) ** 2 <= r * r + 0.3:
                out.add((x, z))
    return out


def ring(r, cx, cz):
    """Outline (4-connected edge cells) of disc(r)."""
    cells = disc(r, cx, cz)
    return {(x, z) for (x, z) in cells
            if any((x + dx, z + dz) not in cells for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))}


SOLIDISH_NO = ("air", "stairs", "slab", "lantern", "torch", "door", "carpet", "flower", "pot", "rail", "chain",
               "bed", "sign", "banner", "button", "plate", "rod", "water", "trapdoor", "leaves", "sapling", "grass",
               "fern", "bush", "lily", "cane", "vine", "candle", "bell", "azalea", "substitution", "head", "campfire")


def connect_walls(d):
    """Set the side connections of every *_wall block (the toolkit only does panes and fences)."""
    bp = d.bp
    dirs = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}
    for x, y, z, s in list(bp.blocks()):
        name = s.split("[")[0]
        if not name.endswith("_wall") or "sign" in name or "banner" in name or "torch" in name:
            continue
        sides = {}
        for k, (dx, dz) in dirs.items():
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


def river(d, x1, x2, bed=("gravel", "clay", "sand"), weir="mossy_stone_bricks", lily=()):
    """River channel along z between x1..x2: water in the ground layer, riverbed below, low weirs at the plot ends
    so the water stays inside the plot."""
    for x in range(x1, x2 + 1):
        for z in range(d.sz):
            d.set(x, 0, z, "structurize:blocksolidsubstitution")
            d.set(x, 1, z, weir if z in (0, d.sz - 1) else WATER)
    for x, z in lily:                                     # lily pads at hand-picked spots
        d.set(x, 2, z, "lily_pad")


def tree(d, x, z, y=2, h=4, log="oak_log", leaves="oak_leaves", r=2):
    for k in range(h):
        d.set(x, y + k, z, f"{log}[axis=y]")
    top = y + h
    for dy in range(-1, 2):
        rr = r if dy < 1 else r - 1
        for dx in range(-rr, rr + 1):
            for dz in range(-rr, rr + 1):
                if abs(dx) + abs(dz) > rr + (1 if dy < 0 else 0):
                    continue
                xx, zz, yy = x + dx, z + dz, top + dy
                if d.bp.inside(xx, yy, zz) and d.air(xx, yy, zz):
                    d.set(xx, yy, zz, f"{leaves}[distance=1,persistent=true,waterlogged=false]")
    d.set(x, top - 1, z, f"{log}[axis=y]")


def lamppost(d, x, z, y=2, h=3, post="dark_oak_fence", head=None):
    for k in range(h):
        d.set(x, y + k, z, post)
    d.set(x, y + h, z, head or lantern())


UNDER = {"Hearthwood": ("gravel", "coarse_dirt"), "Cascadia": ("coarse_dirt", "rooted_dirt"),
         "Neoterra": ("smooth_stone", "moss_block")}


def undercover(d):
    """Material swap: grass does not grow under eaves, canopies and tree crowns. Every open grass cell of the
    ground layer with a roof or a tree crown above it becomes a drip strip (eaves) or a mulched tree pit."""
    eave, pit = UNDER[d.pack]
    bp = d.bp
    for z in range(bp.sz):
        for x in range(bp.sx):
            if not bp.get(x, 1, z).startswith("minecraft:grass_block") or bp.get(x, 2, z) != AIR:
                continue
            for y in range(4, min(bp.sy, 15)):
                st = bp.get(x, y, z)
                if st != AIR:
                    bp.grid[1][z][x] = f"minecraft:{pit if 'leaves' in st else eave}"
                    break
    return d


def wing_design(pack, rel, size):
    return Design(pack, rel, size, gy=0, paving=None)


def wonder_path(name):
    return f"{ROOT}{name}wing0.blueprint"


# =============================================================================================================
#                                                 GRAND BRIDGE
# =============================================================================================================
# geometry shared between parents and wings: plot, wing reserve box (parent coords), wing size, child hut cell
GB = {
    "Hearthwood": dict(size=(33, 30, 23), zc=11, res=(0, 4, 7, 15), wsize=(5, 22, 9), whut=(2, 1, 2)),
    "Cascadia": dict(size=(33, 30, 21), zc=10, res=(0, 6, 6, 14), wsize=(7, 26, 9), whut=(3, 1, 0)),
    "Neoterra": dict(size=(33, 32, 27), zc=13, res=(1, 5, 7, 19), wsize=(5, 30, 13), whut=(2, 1, 2)),
}


def gb_place_wings(d, g, path):
    x1, x2, z1, z2 = g["res"]
    sx = d.sx
    wx, wy, wz = g["wsize"]
    hx, hy, hz = g["whut"]
    for ox in (x1, sx - 1 - x2):
        d.reserve(ox, 1, z1, ox + wx - 1, d.sy - 1, z1 + wz - 1)
        d.child_hut(ox + hx, hy + 1, z1 + hz, path)


# ----------------------------------------------------------------------------------------------- Hearthwood
# surface height of the humpbacked road per x (west half; mirrored), ground = 2
HW_S = {7: 3, 8: 4, 9: 5, 10: 6, 11: 6.5, 12: 7, 13: 7.5, 14: 8, 15: 8, 16: 8}
HW_TOWER_TOP = {1: 4, 2: 7, 3: 9, 4: 11, 5: 11}


def hw_s(x):
    return HW_S.get(x if x <= 16 else 32 - x, 2)


def core_gb_hearthwood(rel, L):
    g = GB["Hearthwood"]
    d = Design("Hearthwood", rel, g["size"], gy=1, paving="grass_block[snowy=false]")
    zc = g["zc"]
    zr1, zr2 = zc - 1, zc + 1                         # roadway
    zb1, zb2 = zc - 2, zc + 2                         # bridge body (parapets on these rows)
    stone, sst, sslab, swall = "stone_bricks", "stone_brick_stairs", "stone_brick_slab", "stone_brick_wall"
    river(d, 9, 23, lily=((10, 3), (12, 5), (21, 2), (20, 18), (11, 19), (22, 20)) if L >= 3 else ())
    # banks: stone quay edge, gravel road to the towers
    for z in range(1, d.sz - 1):
        for x in (8, 24):
            d.set(x, 1, z, "mossy_stone_bricks" if (z * 5) % 7 == 0 else stone)
    for x in list(range(0, 9)) + list(range(24, 33)):
        for z in range(zr1, zr2 + 1):
            d.set(x, 1, z, "gravel" if L < 3 else ("cobblestone" if (x + z) % 3 else "mossy_cobblestone"))
    # ---------- bridge body
    arches = {9: 2, 10: 3, 11: 3, 12: 2, 14: 3, 15: 4, 16: 4, 17: 4, 18: 3}
    for x in range(7, 26):
        s = hw_s(x)
        top = int(s) - 1                               # highest full block
        half = s != int(s)
        base = 1 if 9 <= x <= 23 else 2
        rise = 1 if x < 16 else -1
        for z in range(zb1, zb2 + 1):
            for y in range(base, top + 1):
                d.set(x, y, z, stone)
            edge = z in (zb1, zb2)
            if half:
                d.set(x, top + 1, z, stone if edge else slab(sslab))
                ptop = top + 2
            else:
                stepped = abs(hw_s(x) - hw_s(x - rise)) >= 1 if x != 16 else False
                if not edge and stepped:
                    d.set(x, top, z, stair(sst, "east" if x < 16 else "west"))
                ptop = top + 1
            if edge:
                d.set(x, ptop, z, swall if L < 3 or x in (7, 25) else "stone_bricks")
                if L >= 3 and x not in (7, 25):
                    d.set(x, ptop + 1, z, slab(sslab))
        # arches through the body
        xa = x if x <= 16 else 32 - x
        h = arches.get(xa)
        if h:
            for z in range(zb1, zb2 + 1):
                for y in range(2, 2 + h):
                    d.set(x, y, z, AIR)
                d.set(x, 1, z, WATER)
                # round the arch shoulders with upside-down stairs
            nxt = arches.get(xa + 1) if x <= 16 else arches.get(xa - 1)
            prv = arches.get(xa - 1) if x <= 16 else arches.get(xa + 1)
            for z in range(zb1, zb2 + 1):
                if not prv:
                    d.set(x, 1 + h, z, stair(sst, "west" if x <= 16 else "east", "top"))
                elif not nxt:
                    d.set(x, 1 + h, z, stair(sst, "east" if x <= 16 else "west", "top"))
    # arch rings (voussoirs) on both faces from L3
    if L >= 3:
        for x in range(9, 24):
            xa = x if x <= 16 else 32 - x
            h = arches.get(xa)
            if not h:
                continue
            for z in (zb1, zb2):
                y = 2 + h
                if d.get(x, y, z) == "minecraft:stone_bricks":
                    d.set(x, y, z, "polished_andesite")
            for z in (zb1, zb2):
                for xx in (x - 1, x + 1):
                    xa2 = xx if xx <= 16 else 32 - xx
                    if not arches.get(xa2):
                        for y in range(2, 2 + h + 1):
                            if d.get(xx, y, z) == "minecraft:stone_bricks":
                                d.set(xx, y, z, "polished_andesite")
    # string course along both faces under the parapet
    if L >= 2:
        for x in range(8, 25):
            s = hw_s(x)
            y = int(s) - 1
            for z, f in ((zb1 - 1, "south"), (zb2 + 1, "north")):
                if d.air(x, y, z):
                    d.set(x, y, z, stair(sst, f, "top"))
    # piers with cutwaters, up and downstream
    for px in (13, 19):
        for z0, dz in ((zb1 - 1, -1), (zb2 + 1, 1)):
            ytop = 3 if L < 3 else int(hw_s(px)) - 2
            for x in (px - 1, px, px + 1):
                for y in range(1, ytop + 1):
                    d.set(x, y, z0, stone)
            for y in range(1, ytop):
                d.set(px, y, z0 + dz, stone)
            cap = stair(sst, "south" if dz < 0 else "north")
            for x in (px - 1, px + 1):
                d.set(x, ytop + 1, z0, stair(sst, "east" if x < px else "west"))
            d.set(px, ytop + 1, z0, stone if L >= 3 else cap)
            d.set(px, ytop, z0 + dz, cap)
            if L >= 4:                                   # statue plinth over each cutwater on the parapet
                yb = int(hw_s(px)) + 1
                d.set(px, ytop + 1, z0, stone)
                for y in range(ytop + 2, yb):
                    d.set(px, y, z0, stone)
                d.set(px, yb, z0, "chiseled_stone_bricks")
                d.set(px, yb + 1, z0, "stone_brick_wall")
                d.set(px, yb + 2, z0, lantern())
    # moss and ivy on the old stone
    if L >= 2:
        for x in range(9, 24):
            for z in (zb1, zb2):
                if d.get(x, 2, z) == "minecraft:stone_bricks" and (x * 3 + z) % 4 == 0:
                    d.set(x, 2, z, "mossy_stone_bricks")
    # ---------- central refuge bay (downstream) with the hut; L4 a shrine canopy, L5 a little chantry
    yb = int(hw_s(16)) - 1                             # deck block y (7); walk y 8
    for x in range(14, 19):
        for z in range(zb2 + 1, zb2 + 4):
            d.set(x, yb, z, stone)
        d.set(x, yb - 1, zb2 + 1, stair(sst, "south", "top"))
        d.set(x, yb - 1, zb2 + 2, stair(sst, "north", "top"))
        d.set(x, yb - 2, zb2 + 1, stair(sst, "north", "top"))
    for x in range(15, 18):
        d.set(x, yb + 1, zb2, AIR)
        d.set(x, yb + 2, zb2, AIR)
        for z in range(zb2 + 1, zb2 + 3):
            d.set(x, yb + 1, z, AIR)
    for x in range(14, 19):
        d.set(x, yb + 1, zb2 + 3, swall)
    for z in range(zb2 + 1, zb2 + 3):
        d.set(14, yb + 1, z, swall)
        d.set(18, yb + 1, z, swall)
    d.hut(16, yb + 1, zb2 + 2, "north")
    d.chair(15, yb + 1, zb2 + 2, "south", "dark_oak", sit=False)
    d.chair(17, yb + 1, zb2 + 2, "south", "dark_oak", sit=False)
    d.set(14, yb + 2, zb2 + 3, lantern())
    d.set(18, yb + 2, zb2 + 3, lantern())
    if L >= 4:
        top = yb + 5
        for x, z in ((14, zb2 + 1), (18, zb2 + 1), (14, zb2 + 3), (18, zb2 + 3)):
            for y in range(yb + 1, top):
                d.set(x, y, z, "stone_brick_wall" if L == 4 else stone)
        if L >= 5:
            for x in range(14, 19):
                for y in range(yb + 1, top):
                    d.set(x, y, zb2 + 3, stone)
            for z in range(zb2 + 1, zb2 + 3):
                for y in range(yb + 1, top):
                    d.set(14, y, z, stone)
                    d.set(18, y, z, stone)
            d.set(16, yb + 3, zb2 + 3, "glass_pane")
            d.set(16, yb + 4, zb2 + 3, "glass_pane")
            d.set(14, yb + 3, zb2 + 2, "glass_pane")
            d.set(18, yb + 3, zb2 + 2, "glass_pane")
            d.set(15, yb + 2, zb2 + 2, "candle[candles=3,lit=false,waterlogged=false]")
        r = d.hip(14, zb2 + 1, 18, zb2 + 3, top, "deepslate_tile_stairs", "deepslate_tile_slab", overhang=0)
        d.set(16, r + 1, zb2 + 2, "stone_brick_wall")
        d.set(16, r + 2, zb2 + 2, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        d.set(16, top - 1, zb2 + 2, lantern(True))
        if L >= 5:
            d.set(16, top - 2, zb2 + 2, AIR)
    # ---------- lamps at the bridge ends, banks
    for x in (7, 25):
        for z in (zb1, zb2):
            d.set(x, 3, z, stone)
            d.set(x, 4, z, lantern() if L >= 2 else swall)
    # river banks: willows, reeds, benches
    if L >= 2:
        for z in list(range(2, 6)) + list(range(17, 21)):
            for x in (9, 23):
                if z % 2 == 0:
                    d.set(x, 1, z, "grass_block[snowy=false]")
                    d.set(x, 2, z, "sugar_cane")
    if L >= 3:
        tree(d, 3, 2, h=4, leaves="oak_leaves")
        tree(d, 29, 20, h=4, leaves="oak_leaves")
    if L >= 4:
        tree(d, 29, 2, h=5, leaves="dark_oak_leaves", log="dark_oak_log")
        tree(d, 3, 20, h=5, leaves="dark_oak_leaves", log="dark_oak_log")
        for x, z, f in ((5, 4, "south"), (27, 18, "north")):
            d.chair(x, 2, z, f, "oak", sit=False)
            d.chair(x - 1, 2, z, f, "oak", sit=False)
    if L >= 5:
        for x in range(1, 8):
            d.set(x, 2, 0, "oak_fence") if x % 2 else d.set(x, 2, 0, "potted_red_tulip")
        for x, z in ((1, 17), (1, 18), (31, 4), (31, 5), (30, 4)):
            d.set(x, 2, z, ("rose_bush[half=lower]", "peony[half=lower]", "lilac[half=lower]")[(x + z) % 3])
            d.set(x, 3, z, ("rose_bush[half=upper]", "peony[half=upper]", "lilac[half=upper]")[(x + z) % 3])
    gb_place_wings(d, g, wonder_path("grandbridge"))
    connect_walls(d)
    return d


def gbw_hearthwood(rel, L):
    g = GB["Hearthwood"]
    d = wing_design("Hearthwood", rel, g["wsize"])
    W, _, D = g["wsize"]                                 # 5 x 9: body z1..7, parapet corbelled out to z0..8
    top = HW_TOWER_TOP[L]
    stone, sst = "stone_bricks", "stone_brick_stairs"
    d.fill(0, 0, 0, W - 1, 0, D - 1, "cobblestone")
    d.fill(0, 0, 3, W - 1, 0, 5, "gravel")
    d.box(0, 1, 1, W - 1, top, D - 2, stone)
    d.fill(1, 1, 2, W - 2, top, 2, stone)               # passage walls (and the walls of the rooms above)
    d.fill(1, 1, 6, W - 2, top, 6, stone)
    d.clear(0, 1, 3, W - 1, 4, 5)
    for x in range(W):
        d.set(x, 4, 3, stair(sst, "north", "top"))
        d.set(x, 4, 5, stair(sst, "south", "top"))
    for fy in range(5, top + 1, 4):                      # floors of the rooms above the gate
        d.fill(1, fy, 3, W - 2, fy, 5, "oak_planks")
    d.fill(0, 5, 3, W - 1, 5, 5, stone)
    # quoins and a mossy plinth
    for y in range(1, top + 1):
        for x, z in ((0, 1), (W - 1, 1), (0, D - 2), (W - 1, D - 2)):
            d.set(x, y, z, "polished_andesite" if (y % 2 == 0 and L >= 2) else stone)
    for x in range(W):
        for z in (1, D - 2):
            d.set(x, 1, z, "mossy_stone_bricks" if (x + z) % 2 else "cobblestone")
    d.hut(*g["whut"], facing="south")
    # portcullis teeth and a lantern in the vault
    if L >= 2:
        for z in range(3, 6):
            d.set(0, 4, z, "iron_bars")
    d.set(2, 4, 4, lantern(True))
    # arch ring on both passage faces
    if L >= 3:
        for x in (0, W - 1):
            for z in (2, 6):
                for y in range(1, 5):
                    d.set(x, y, z, "polished_andesite")
            for z in range(2, 7):
                d.set(x, 5, z, "chiseled_stone_bricks" if z == 4 else "polished_andesite")
    # leaded windows on the long faces, arrow slits over the gate
    for fy in range(6, top - 1, 4):
        for z in (1, D - 2):
            d.set(2, fy, z, "glass_pane")
            d.set(2, fy + 1, z, "glass_pane")
        for x in (0, W - 1):
            d.set(x, fy + 1, 4, "glass_pane")
    # machicolated parapet: corbelled out over the street and back faces
    py = top + 1
    for x in range(W):
        d.set(x, top, 0, stair(sst, "south", "top"))
        d.set(x, top, D - 1, stair(sst, "north", "top"))
    d.fill(0, py, 0, W - 1, py, D - 1, stone)
    for x in range(W):
        for z in range(D):
            if x in (0, W - 1) or z in (0, D - 1):
                d.set(x, py + 1, z, stone)
                if (x + z) % 2 == 0:
                    d.set(x, py + 2, z, stone)
    if L >= 3:
        for x in (0, W - 1):
            d.banner(x, top - 1, 4, "west" if x == 0 else "east", "red")
        for x in range(W):
            for z in range(D):
                if (x in (0, W - 1) or z in (0, D - 1)) and (x + z) % 2 == 0:
                    d.set(x, py + 2, z, "chiseled_stone_bricks" if x in (0, W - 1) and z in (0, D - 1) else stone)
    if L >= 4:                                           # corner pinnacles
        for x, z in ((0, 0), (W - 1, 0), (0, D - 1), (W - 1, D - 1)):
            d.set(x, py + 2, z, stone)
            d.set(x, py + 3, z, "stone_brick_wall")
            d.set(x, py + 4, z, lantern())
    if L >= 5:                                           # steep slate roof with a lead flèche
        for x in range(1, W - 1):
            for z in range(1, D - 1):
                pass
        for z in range(1, D - 1):
            for x in (1, W - 2):
                d.set(x, py + 1, z, "deepslate_tiles")
                d.set(x, py + 2, z, stair("deepslate_tile_stairs", "east" if x == 1 else "west"))
            for y in range(py + 1, py + 4):
                d.set(2, y, z, "deepslate_tiles")
            d.set(2, py + 4, z, slab("deepslate_tile_slab"))
        for z in (1, D - 2):
            d.set(2, py + 4, z, stair("deepslate_tile_stairs", "south" if z == 1 else "north"))
        d.set(2, py + 4, 4, "deepslate_tiles")
        d.set(2, py + 5, 4, "deepslate_tile_wall")
        d.set(2, py + 6, 4, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    connect_walls(d)
    return d


# ----------------------------------------------------------------------------------------------- Cascadia
CA_DECK = 6                                              # walk height of the covered deck
CA_TOWER = {1: 5, 2: 8, 3: 10, 4: 12, 5: 14}


def core_gb_cascadia(rel, L):
    g = GB["Cascadia"]
    d = Design("Cascadia", rel, g["size"], gy=1, paving="grass_block[snowy=false]")
    zc = g["zc"]
    zw1, zw2 = zc - 3, zc + 3                            # side walls / trusses
    zr1, zr2 = zc - 2, zc + 2                            # roadway
    Y = CA_DECK
    log, slog, pl = "spruce_log", "stripped_spruce_log", "spruce_planks"
    river(d, 11, 21, bed=("gravel", "cobblestone", "gravel", "mossy_cobblestone"), weir="mossy_cobblestone",
          lily=())
    for z in range(1, d.sz - 1):
        for x in (10, 22):
            d.set(x, 1, z, ("cobblestone", "mossy_cobblestone", "andesite", "tuff")[(z * 3 + x) % 4])
    for x in list(range(0, 11)) + list(range(22, 33)):
        for z in range(zr1, zr2 + 1):
            d.set(x, 1, z, "coarse_dirt" if (x + z) % 4 else "gravel")
    # abutments: river-rock cribs with log ramps
    for x0, xs, f in ((7, 1, "east"), (25, -1, "west")):
        for i in range(4):
            x = x0 + xs * i
            for z in range(zw1, zw2 + 1):
                for y in range(1, 2 + i):
                    d.set(x, y, z, ("cobblestone", "mossy_cobblestone", "andesite")[(x + y + z) % 3]
                          if z in (zw1, zw2) or y < 1 + i else pl)
                if i < 3:
                    d.set(x, 2 + i, z, stair("spruce_stairs", f) if zr1 <= z <= zr2 else
                          ("cobblestone" if L < 3 else "mossy_cobblestone"))
                else:
                    d.set(x, Y - 1, z, pl)
    # deck: planks across, log stringers below
    for x in range(10, 23):
        for z in range(zw1, zw2 + 1):
            d.set(x, Y - 1, z, pl if zr1 <= z <= zr2 else f"{log}[axis=x]")
        for z in (zr1, zc, zr2):
            d.set(x, Y - 2, z, f"{log}[axis=x]")
    # trestle bents in the river
    for bx in (13, 16, 19):
        for z in range(zw1, zw2 + 1, 2):
            d.set(bx, 1, z, "cobblestone")
            for y in range(2, Y - 1):
                d.set(bx, y, z, f"{log}[axis=y]")
        for z in range(zw1, zw2 + 1):
            d.set(bx, Y - 2, z, f"{log}[axis=z]")
            if d.air(bx, 3, z):
                d.set(bx, 3, z, f"{slog}[axis=z]")
        for z in (zw1 - 1, zw2 + 1):                        # raked outer posts
            d.set(bx, 1, z, "mossy_cobblestone")
            d.set(bx, 2, z, f"{log}[axis=y]")
            d.set(bx, 3, z, stair("spruce_stairs", "south" if z < zc else "north", "top"))
    # knee braces under the stringers
    for bx in (13, 16, 19):
        for x, f in ((bx - 1, "east"), (bx + 1, "west")):
            for z in (zw1, zw2):
                d.set(x, Y - 2, z, stair("spruce_stairs", f, "top"))
    # ---- superstructure by level
    X1, X2 = 10, 22
    if L == 1:                                            # open log bridge with a rail
        for x in range(X1, X2 + 1):
            for z in (zw1, zw2):
                d.set(x, Y, z, "spruce_fence")
                if (x - X1) % 3 == 0:
                    d.set(x, Y, z, f"{log}[axis=y]")
                    d.set(x, Y + 1, z, lantern() if x in (X1, X2) else "spruce_fence")
    else:
        H = 4                                             # wall / truss height
        for x in range(X1, X2 + 1):
            for z in (zw1, zw2):
                d.set(x, Y + H - 1, z, f"{log}[axis=x]")    # top chord
                d.set(x, Y, z, f"{slog}[axis=x]")           # bottom rail
            if (x - X1) % 3 == 0:
                for z in (zw1, zw2):
                    for y in range(Y, Y + H):
                        d.set(x, y, z, f"{log}[axis=y]")
        # Howe truss diagonals (fence lattice) between the posts
        for x in range(X1, X2):
            k = (x - X1) % 3
            if k == 0:
                continue
            for z in (zw1, zw2):
                yy = Y + (k if x < 16 else 3 - k)
                d.set(x, yy, z, "dark_oak_fence")
        # tie beams across the top
        for x in range(X1, X2 + 1, 3):
            for z in range(zw1, zw2 + 1):
                d.set(x, Y + H, z, f"{log}[axis=z]")
        if L >= 3:                                        # siding + roof = covered bridge
            for x in range(X1, X2 + 1):
                for z in (zw1, zw2):
                    for y in range(Y + 1, Y + H - 1):
                        if (x - X1) % 3:
                            d.set(x, y, z, "mangrove_planks")
            ridge = d.gable(X1, zw1, X2, zw2, Y + H, "x", "dark_oak_stairs", "dark_oak_slab", "spruce_planks",
                            overhang=1)
            # portals: board gable ends with the opening below
            for x in (X1, X2):
                for z in range(zw1, zw2 + 1):
                    d.set(x, Y + H, z, f"{slog}[axis=z]")
                for z in range(zr1, zr2 + 1):
                    for y in range(Y, Y + H):
                        d.set(x, y, z, AIR)
                for z in (zr1, zr2):
                    d.set(x, Y + H - 1, z, stair("spruce_stairs", "south" if z == zr1 else "north", "top"))
            for x in range(X1 + 1, X2):
                d.set(x, ridge - 1, zc, f"{log}[axis=x]")
            if L >= 4:                                    # daylight windows under the eaves
                for x in range(X1 + 1, X2):
                    if (x - X1) % 3:
                        for z in (zw1, zw2):
                            d.set(x, Y + 2, z, "glass_pane")
                for x in range(X1 + 2, X2, 3):
                    d.set(x, Y + H - 1, zc, lantern(True))
            if L >= 5:                                    # portal false fronts with the crossing's name
                for x, f in ((X1 - 1, "west"), (X2 + 1, "east")):
                    for z in range(zw1 - 1, zw2 + 2):
                        for y in range(Y + H - 1, ridge + 2):
                            if not (zr1 <= z <= zr2 and y < Y + H):
                                d.set(x, y, z, "mangrove_planks" if zw1 <= z <= zw2 else f"{log}[axis=y]")
                    for z in range(zw1 - 1, zw2 + 2):
                        d.set(x, ridge + 2, z, slab("spruce_slab"))
                    for dz in (-1, 0, 1):
                        d.sign(x + (-1 if f == "west" else 1), ridge, zc + dz, f,
                               (["CASCADIA", "CROSSING"] if dz == 0 else ["~", "EST 1889"]), "spruce")
                    for y in range(Y, Y + H - 1):
                        for z in (zw1 - 1, zw2 + 1):
                            d.set(x, y, z, f"{log}[axis=y]")
    # hut: toll box against the south wall, middle of the span
    d.hut(16, Y, zr2, "north")
    d.set(15, Y, zr2, "barrel[facing=up,open=false]")
    # side gallery (L4+): cantilevered walkway on the downstream side
    if L >= 4:
        zg = zw2 + 1
        for x in range(X1 + 1, X2):
            d.set(x, Y - 1, zg, "spruce_planks")
            d.set(x, Y - 1, zg + 1, "spruce_planks")
            d.set(x, Y - 2, zg + 1, stair("spruce_stairs", "north", "top"))
            d.set(x, Y, zg + 1, "spruce_fence")
            d.set(x, Y + 3, zg, stair("spruce_stairs", "north"))
            d.set(x, Y + 3, zg + 1, stair("spruce_stairs", "north"))
        for x in range(X1 + 1, X2, 3):
            d.set(x, Y, zg + 1, f"{log}[axis=y]")
            d.set(x, Y + 1, zg + 1, f"{log}[axis=y]")
            d.set(x, Y + 2, zg + 1, f"{log}[axis=y]")
        for x in range(X1 + 2, X2 - 1, 3):
            d.set(x, Y, zw2, AIR)
            d.set(x, Y + 1, zw2, AIR)
        for x in range(X1 + 1, X2):
            if d.get(x, Y + 3, zg + 1).endswith("_log[axis=y]"):
                d.set(x, Y + 3, zg + 1, stair("spruce_stairs", "north"))
    # banks: firs, boulders, rail fence along the road
    if L >= 2:
        for x, z in ((3, 1), (29, 18), (8, 18)):
            tree(d, x, z, h=5, log="spruce_log", leaves="spruce_leaves", r=1)
        for x, z in ((24, 2), (9, 2)):
            d.set(x, 2, z, "mossy_cobblestone")
            d.set(x + 1 if x < 30 else x - 1, 2, z, "cobblestone_slab[type=bottom,waterlogged=false]")
    if L >= 3:
        for z in (zr1 - 1, zr2 + 1):
            for x in list(range(7, 10)) + list(range(23, 26)):
                pass
        for x, z in ((2, 18), (30, 2)):
            tree(d, x, z, h=6, log="spruce_log", leaves="spruce_leaves", r=2)
    if L >= 4:
        for x, z in ((8, 3), (24, 17)):
            lamppost(d, x, z, post="spruce_fence")
        for x in (13, 16, 19):
            d.set(x, 2, 2, "lily_pad")
    if L >= 5:
        for x, z in ((5, 2), (27, 18), (6, 18)):
            d.keg(x, 2, z, "east")
            d.set(x, 3, z, "potted_fern")
        for x, z in ((26, 1), (26, 2), (4, 18)):
            d.set(x, 2, z, "hay_block[axis=y]")
    gb_place_wings(d, g, wonder_path("grandbridge"))
    connect_walls(d)
    return d


def gbw_cascadia(rel, L):
    """Timber lookout tower straddling the road: four log legs with girts and cross bracing, a lookout cabin on top."""
    g = GB["Cascadia"]
    d = wing_design("Cascadia", rel, g["wsize"])
    W, _, D = g["wsize"]                                 # 7 x 9, road z2..6
    log, slog = "spruce_log", "stripped_spruce_log"
    d.fill(0, 0, 0, W - 1, 0, D - 1, "coarse_dirt")
    d.fill(0, 0, 2, W - 1, 0, D - 3, "gravel")
    P = CA_TOWER[L]                                      # platform floor y (L1: portal beam)
    legs = [(1, 0), (W - 2, 0), (1, D - 1), (W - 2, D - 1)]
    for x, z in legs:
        d.set(x, 0, z, "cobblestone")
        d.set(x, 1, z, "mossy_cobblestone")
        for y in range(2, P + 1):
            d.set(x, y, z, f"{log}[axis=y]")
    # girts on the outer faces every 4, X bracing between them (not across the road)
    for z in (0, D - 1):
        for y in range(5, P, 4):
            for x in range(2, W - 2):
                d.set(x, y, z, f"{slog}[axis=x]")
        for yb in range(1, P - 3, 4):
            for k in range(3):
                d.set(2 + k, yb + 1 + k, z, "spruce_fence")
                d.set(W - 3 - k, yb + 1 + k, z, "spruce_fence")
    # beams over the road (on the leg lines), with the crossing's sign
    for x in (1, W - 2):
        for z in range(1, D - 1):
            d.set(x, 5, z, f"{log}[axis=z]")
        d.set(x, 4, 1, stair("spruce_stairs", "north", "top"))
        d.set(x, 4, D - 2, stair("spruce_stairs", "south", "top"))
    for f, x in (("west", 0), ("east", W - 1)):
        for z in range(3, 6):
            d.set(x, 5, z, "spruce_planks")
    d.hut(3, 1, 0, "south")
    d.set(2, 1, 0, "barrel[facing=up,open=false]")
    if L == 1:
        for x in (1, W - 2):
            d.set(x, 6, 0, lantern())
            d.set(x, 6, D - 1, lantern())
        for x in range(1, W - 1):
            for z in (0, D - 1):
                if x not in (1, W - 2):
                    d.set(x, 5, z, f"{slog}[axis=x]")
        connect_walls(d)
        return d
    # platform with a rail
    d.fill(0, P + 1, 0, W - 1, P + 1, D - 1, "spruce_planks")
    for x in range(W):
        for z in range(D):
            if x in (0, W - 1) or z in (0, D - 1):
                d.set(x, P + 2, z, "spruce_fence")
    for x in range(W):
        d.set(x, P, 0, stair("spruce_stairs", "south", "top")) if x in (0, W - 1) else None
    for z in range(D):
        d.set(0, P, z, stair("spruce_stairs", "east", "top"))
        d.set(W - 1, P, z, stair("spruce_stairs", "west", "top"))
    # ladder up the north-west leg
    for y in range(1, P + 2):
        d.set(1, y, 1, "ladder[facing=south,waterlogged=false]")
    d.set(1, P + 2, 1, AIR)
    if L == 2:
        for x, z in ((0, 0), (W - 1, 0), (0, D - 1), (W - 1, D - 1)):
            d.set(x, P + 3, z, lantern())
        connect_walls(d)
        return d
    # lookout cabin
    cy = P + 2
    ch = 3
    x1, x2, z1, z2 = 1, W - 2, 2, D - 3
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                corner = x in (x1, x2) and z in (z1, z2)
                for y in range(cy, cy + ch):
                    if corner:
                        st = f"{log}[axis=y]"
                    elif y == cy:
                        st = f"{slog}[axis=x]" if z in (z1, z2) else f"{slog}[axis=z]"
                    else:
                        st = "glass_pane" if L >= 4 else ("spruce_trapdoor[facing=" + ("north" if z == z1 else "south" if z == z2 else "west" if x == x1 else "east") + ",half=bottom,open=true,powered=false,waterlogged=false]")
                    d.set(x, y, z, st)
    d.door(3, cy, z1, "north", "spruce")
    d.set(3, cy + ch - 1, 4, lantern(True))
    d.set(2, cy, 4, "cartography_table") if L >= 4 else None
    d.set(4, cy, 4, "spruce_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]")
    r = d.hip(x1, z1, x2, z2, cy + ch, "dark_oak_stairs", "dark_oak_slab", overhang=1)
    d.set(3, r + 1, 4, "spruce_fence")
    if L >= 5:
        d.set(3, r + 2, 4, "spruce_fence")
        d.set(3, r + 3, 4, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        for x, z in ((0, 0), (W - 1, 0), (0, D - 1), (W - 1, D - 1)):
            d.set(x, P + 3, z, lantern())
    connect_walls(d)
    return d


# ----------------------------------------------------------------------------------------------- Neoterra
NT_PYLON = {1: 6, 2: 11, 3: 15, 4: 19, 5: 23}            # child y of the top crossbeam
NT_S = {6: 2, 7: 2.5, 8: 3, 9: 3.5, 10: 4, 11: 4.5, 12: 5, 13: 5, 14: 5, 15: 5, 16: 5}


def nt_s(x):
    return NT_S.get(x if x <= 16 else 32 - x, 2)


def core_gb_neoterra(rel, L):
    g = GB["Neoterra"]
    d = Design("Neoterra", rel, g["size"], gy=1, paving="grass_block[snowy=false]")
    zc = g["zc"]
    ze1, ze2 = zc - 3, zc + 3                            # deck edges (glass rails)
    river(d, 10, 22, bed=("sand", "gravel", "clay"), weir="smooth_stone", lily=())
    for z in range(1, d.sz - 1):
        for x in (9, 23):
            d.set(x, 1, z, "smooth_stone")
    for x in list(range(0, 10)) + list(range(23, 33)):
        for z in range(ze1, ze2 + 1):
            d.set(x, 1, z, "gray_concrete" if ze1 < z < ze2 else "light_gray_concrete")
        d.set(x, 1, zc, "white_concrete" if x % 3 == 0 else "gray_concrete")
    # ---- deck
    for x in range(6, 27):
        s = nt_s(x)
        top = int(s) - 1
        half = s != int(s)
        for z in range(ze1, ze2 + 1):
            road = ze1 < z < ze2
            if top >= 1:
                d.set(x, top, z, ("gray_concrete" if road else "light_gray_concrete"))
                if top >= 2:
                    under = top - 1
                    if z in (ze1, ze2):
                        d.set(x, under, z, stair("smooth_quartz_stairs", "south" if z == ze1 else "north", "top"))
            if half:
                d.set(x, top + 1, z, slab("smooth_stone_slab" if road else "smooth_quartz_slab"))
            if z == zc and not half and x % 3 == 0 and top >= 1:
                d.set(x, top, z, "white_concrete")
        # glass railings on the edges
        ry = (top + 2) if half else (top + 1)
        for z in (ze1, ze2):
            if half:
                d.set(x, top + 1, z, "smooth_quartz")
            d.set(x, ry, z, "glass_pane" if L < 4 else "light_blue_stained_glass_pane")
    # abutment walls at the banks
    for x in (8, 9, 23, 24):
        for z in range(ze1, ze2 + 1):
            top = int(nt_s(x)) - 1
            for y in range(2, top):
                d.set(x, y, z, "white_concrete")
    # V piers in the river (L1+), slim columns
    for px in (13, 19):
        for z in (ze1 + 1, ze2 - 1):
            d.set(px, 1, z, "light_gray_concrete")
            d.set(px, 2, z, "white_concrete")
            d.set(px, 3, z, "white_concrete")
        for z in range(ze1, ze2 + 1):
            d.set(px, 3, z, "white_concrete")
        d.set(px, 2, zc, "light_gray_concrete")
        d.set(px, 1, zc, "light_gray_concrete")
    # ---- belvedere with the hut on the downstream side
    by = int(nt_s(16)) - 1
    for x in range(14, 19):
        for z in range(ze2 + 1, ze2 + 3):
            d.set(x, by, z, "smooth_quartz")
        d.set(x, by - 1, ze2 + 1, stair("smooth_quartz_stairs", "north", "top"))
        d.set(x, by + 1, ze2 + 3, "glass_pane" if L < 4 else "light_blue_stained_glass_pane")
        d.set(x, by, ze2 + 3, "smooth_quartz_slab[type=top,waterlogged=false]")
    for z in range(ze2 + 1, ze2 + 3):
        d.set(13, by + 1, z, "glass_pane" if L < 4 else "light_blue_stained_glass_pane")
        d.set(19, by + 1, z, "glass_pane" if L < 4 else "light_blue_stained_glass_pane")
        d.set(13, by, z, "smooth_quartz")
        d.set(19, by, z, "smooth_quartz")
    for x in range(15, 18):
        d.set(x, by + 1, ze2, AIR)
    d.hut(16, by + 1, ze2 + 2, "north")
    d.chair(14, by + 1, ze2 + 2, "south", "birch", sit=False)
    d.chair(18, by + 1, ze2 + 2, "south", "birch", sit=False)
    if L >= 3:
        d.set(15, by + 1, ze2 + 2, "potted_bamboo")
        d.set(17, by + 1, ze2 + 2, "potted_bamboo")
    # ---- suspension cables (L2+): main cable on each deck edge, chain hangers
    if L >= 2:
        H = NT_PYLON[L] + 1                                # parent y of the cable at the pylon face
        low = 7
        ys = {}
        for x in range(6, 27):
            t = (x - 16) / 10.0
            ys[x] = round(low + (H - low) * t * t)
        for z in (ze1, ze2):
            for x in range(6, 27):
                nb = ys[x + 1] if x < 16 else ys[x - 1] if x > 16 else ys[x]
                for y in range(min(ys[x], nb + 1), ys[x] + 1):
                    d.set(x, y, z, "diorite_wall")
            for x in range(7, 26):
                if x % 2 == 0:
                    ry = int(nt_s(x)) + (1 if nt_s(x) != int(nt_s(x)) else 0)
                    for y in range(ry + 1, ys[x]):
                        if d.air(x, y, z):
                            d.set(x, y, z, "end_rod[facing=up]")
    # ---- lights along the deck
    if L >= 3:
        for x in range(8, 26, 4):
            for z in (ze1, ze2):
                s = nt_s(x)
                ry = int(s) + (1 if s != int(s) else 0)
                d.set(x, ry, z, "smooth_quartz")
                d.set(x, ry + 1, z, "end_rod[facing=up]" if L < 5 else "sea_lantern")
    # ---- riverside park
    if L >= 2:
        for x0 in (1, 25):
            for z in (2, 22):
                d.set(x0 + 2, 1, z, "white_concrete")
    if L >= 3:
        for x, z in ((4, 2), (28, 23), (4, 23), (28, 2)):
            tree(d, x, z, h=4, log="birch_log", leaves="birch_leaves", r=2)
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                d.set(x + dx, 1, z + dz, "moss_block")
    if L >= 4:
        for z in (4, 21):
            for x in (7, 25):
                d.set(x, 2, z, "smooth_quartz")
                d.set(x, 3, z, "sea_lantern")
        for x in range(10, 23, 3):
            d.set(x, 1, 1, "sea_lantern")
            d.set(x, 1, d.sz - 2, "sea_lantern")
    if L >= 5:
        for x, z in ((6, 3), (26, 22)):
            d.chair(x, 2, z, "south" if z < 10 else "north", "birch", sit=False)
            d.chair(x - 1, 2, z, "south" if z < 10 else "north", "birch", sit=False)
        for x in (1, 31):
            for z in (5, 20):
                d.set(x, 2, z, "white_concrete")
                d.set(x, 3, z, "end_rod[facing=up]")
    gb_place_wings(d, g, wonder_path("grandbridge"))
    connect_walls(d)
    return d


def gbw_neoterra(rel, L):
    g = GB["Neoterra"]
    d = wing_design("Neoterra", rel, g["wsize"])
    W, _, D = g["wsize"]                                 # 5 x 13; legs z0..2 and z10..12, road z3..9
    T = NT_PYLON[L]
    d.fill(0, 0, 0, W - 1, 0, D - 1, "light_gray_concrete")
    d.fill(0, 0, 4, W - 1, 0, D - 5, "gray_concrete")
    for x in range(W):
        d.set(x, 0, 6, "white_concrete" if x % 2 == 0 else "gray_concrete")
    # legs: taper from 3x3 to 1x... keep 3 wide in x (x1..3), 3 deep at the base, 2 above
    for (z1, z2) in ((0, 2), (D - 3, D - 1)):
        for y in range(1, T + 1):
            inset = 1 if y > T // 2 else 0
            zz1 = z1 + (inset if z1 == 0 else 0)
            zz2 = z2 - (inset if z1 != 0 else 0)
            for x in range(1, W - 1):
                for z in range(zz1, zz2 + 1):
                    d.set(x, y, z, "white_concrete")
        # cyan stripe on the inner face and base
        for y in range(1, T + 1, 4):
            for x in range(1, W - 1):
                zi = z2 if z1 == 0 else z1
                if d.get(x, y, zi) == "minecraft:white_concrete":
                    d.set(x, y, zi, "cyan_concrete" if L < 4 else "cyan_terracotta")
        for x in range(0, W):
            for z in range(z1, z2 + 1):
                d.set(x, 1, z, "light_gray_concrete")
    # portal beam (road sign) and top crossbeam
    for z in range(1, D - 1):
        for x in range(0, W):
            d.set(x, T, z, "white_concrete")
            d.set(x, T + 1, z, "smooth_quartz_slab[type=bottom,waterlogged=false]") if x in (0, W - 1) else None
    for x in range(W):
        for z in (0, D - 1):
            d.set(x, T, z, "white_concrete")
    if L >= 3:
        for z in range(1, D - 1):
            d.set(1, T - 1, z, "white_concrete")
            d.set(3, T - 1, z, "white_concrete")
            d.set(2, T - 1, z, "sea_lantern" if L >= 4 else "white_concrete")
        mid = 6
        for z in range(3, D - 3):
            d.set(2, 6, z, "white_concrete") if T > 9 else None
        for x in (1, 3):
            for z in range(3, D - 3):
                d.set(x, 6, z, "light_gray_concrete") if T > 9 else None
    # lower portal beam with the bridge name (above the road, 4 clear)
    if T > 7:
        for z in range(3, D - 3):
            d.set(2, 6, z, "white_concrete")
        d.sign(0, 6, 6, "west", ["SKYLINE", "SPAN"], "birch", glow=True, color="cyan")
        d.sign(4, 6, 6, "east", ["SKYLINE", "SPAN"], "birch", glow=True, color="cyan")
    else:
        d.sign(0, T, 6, "west", ["SKYLINE", "SPAN"], "birch", glow=True, color="cyan")
        d.sign(4, T, 6, "east", ["SKYLINE", "SPAN"], "birch", glow=True, color="cyan")
    # saddle / cable anchors on the crossbeam ends (where the parent's main cables arrive)
    if L >= 2:
        for z in (3, D - 4):
            d.set(W - 1, T + 1, z, "smooth_quartz")
            d.set(0, T + 1, z, "smooth_quartz")
    # aviation lights / crown
    if L >= 4:
        for z in (1, D - 2):
            d.set(2, T + 1, z, "white_concrete")
            d.set(2, T + 2, z, "end_rod[facing=up]" if L == 4 else "sea_lantern")
    if L >= 5:
        for z in range(2, D - 2):
            d.set(2, T + 1, z, "light_blue_stained_glass")
        d.set(2, T + 2, 6, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # hut: service door niche in the north leg
    d.set(2, 1, 2, AIR)
    d.hut(2, 1, 2, "south")
    connect_walls(d)
    return d


@design("grandbridge")
def grandbridge(pack, rel, L):
    return undercover({"Hearthwood": gb_hearthwood, "Cascadia": gb_cascadia, "Neoterra": gb_neoterra}[pack](rel, L))


@design("grandbridgewing")
def grandbridgewing(pack, rel, L):
    return {"Hearthwood": gbw_hearthwood, "Cascadia": gbw_cascadia, "Neoterra": gbw_neoterra}[pack](rel, L)


# =============================================================================================================
#                                                 ROYAL GRANARY
# =============================================================================================================
def cone(d, cx, cz, r0, y0, stairs, cap, step=0.75, solid=None):
    """Conical roof: rings of stairs facing up-slope, radius shrinking by `step` per layer; returns the top y."""
    y, r = y0, r0
    while True:
        cells = disc(r, cx, cz)
        inner = disc(r - step, cx, cz) if r - step > 0.6 else set()
        if not inner:
            for x, z in cells:
                d.set(x, y, z, cap)
            return y
        for x, z in cells - inner:
            dx, dz = x - cx, z - cz
            if abs(dx) >= abs(dz):
                f = "east" if dx < 0 else "west"
            else:
                f = "south" if dz < 0 else "north"
            d.set(x, y, z, stair(stairs, f))
        if solid:
            for x, z in inner:
                if d.air(x, y, z):
                    d.set(x, y, z, solid)
        y += 1
        r -= step


GR = {
    "Hearthwood": dict(size=(33, 26, 27), res=(1, 1), wsize=(9, 20, 9), whut=(3, 1, 2)),
    "Cascadia": dict(size=(31, 34, 31), res=(1, 13), wsize=(9, 30, 9), whut=(3, 1, 2)),
    "Neoterra": dict(size=(33, 26, 31), res=(1, 1), wsize=(7, 24, 7), whut=(2, 1, 1)),
}


def gr_place_wings(d, g, path):
    x1, z1 = g["res"]
    wx, wy, wz = g["wsize"]
    hx, hy, hz = g["whut"]
    for ox in (x1, d.sx - x1 - wx):
        d.reserve(ox, 1, z1, ox + wx - 1, d.sy - 1, z1 + wz - 1)
        d.child_hut(ox + hx, hy + 1, z1 + hz, path)


# ----------------------------------------------------------------------------------------------- Hearthwood
DOVE_H = {1: 4, 2: 5, 3: 6, 4: 7, 5: 8}


def core_rg_hearthwood(rel, L):
    g = GR["Hearthwood"]
    d = Design("Hearthwood", rel, g["size"], gy=1, paving="grass_block[snowy=false]")
    BX1, BX2 = (9, 23) if L == 1 else (3, 29)
    BZ1, BZ2 = 13, 23
    stone, sst = "stone_bricks", "stone_brick_stairs"
    # forecourt
    for x in range(10, 23):
        for z in range(0, BZ1):
            d.set(x, 1, z, "gravel" if (x * 7 + z * 5) % 9 else "coarse_dirt")
    for z in range(0, BZ1):
        for x in (15, 17):
            d.set(x, 1, z, "cobblestone")                   # cart ruts
    # walls
    for x in range(BX1, BX2 + 1):
        for z in range(BZ1, BZ2 + 1):
            d.set(x, 1, z, "packed_mud")
            edge = x in (BX1, BX2) or z in (BZ1, BZ2)
            for y in range(2, 8):
                if edge:
                    if y == 2:
                        st = "mossy_stone_bricks" if (x + z) % 3 == 0 else "cobblestone"
                    else:
                        st = ("smooth_sandstone", "sandstone", "smooth_sandstone", "cut_sandstone", "smooth_sandstone")[(x * 3 + y * 5 + z) % 5]
                    d.set(x, y, z, st)
                else:
                    d.set(x, y, z, AIR)
    for x, z in ((BX1, BZ1), (BX2, BZ1), (BX1, BZ2), (BX2, BZ2)):          # dressed quoins
        for y in range(2, 8):
            d.set(x, y, z, "cut_sandstone" if y % 2 else "chiseled_sandstone")
    # threshing floor between the porch and the back doors
    for x in range(15, 18):
        for z in range(BZ1, BZ2 + 1):
            d.set(x, 1, z, "oak_planks")
    # aisle posts and tie beams
    for x in range(BX1 + 2, BX2 - 1, 4):
        if 14 <= x <= 18:
            continue
        for z in (BZ1 + 2, BZ2 - 2):
            for y in range(2, 8):
                d.set(x, y, z, "dark_oak_log[axis=y]")
            d.set(x - 1, 7, z, stair("dark_oak_stairs", "east", "top"))
            d.set(x + 1, 7, z, stair("dark_oak_stairs", "west", "top"))
        for z in range(BZ1 + 1, BZ2):
            d.set(x, 8, z, "dark_oak_log[axis=z]")
    # roof
    ridge = d.gable(BX1, BZ1, BX2, BZ2, 8, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "smooth_sandstone",
                    overhang=1)
    if L >= 3:                                             # owl holes in the gables
        for x in (BX1, BX2):
            d.set(x, ridge - 2, 18, AIR)
    # ventilation slits on the long walls
    for x in range(BX1 + 2, BX2 - 1, 3):
        if 13 <= x <= 19:
            continue
        for z in (BZ1, BZ2):
            d.set(x, 4, z, AIR)
            d.set(x, 5, z, AIR)
    # porch (midstrey) with the wagon entrance
    PX1, PX2, PZ = 14, 18, 9
    for z in range(PZ, BZ1):
        for x in (PX1, PX2):
            for y in range(2, 7):
                d.set(x, y, z, "smooth_sandstone" if (x + y + z) % 4 else "cut_sandstone")
        for x in range(PX1 + 1, PX2):
            d.set(x, 1, z, "oak_planks")
    for x in range(PX1 + 1, PX2):
        for y in range(2, 6):
            d.set(x, y, BZ1, AIR)
        d.set(x, 6, PZ, "dark_oak_log[axis=x]")
        for y in range(2, 6):
            d.set(x, y, PZ, AIR)
    for x in range(PX1, PX2 + 1):
        d.set(x, 6, PZ, "dark_oak_log[axis=x]") if x in (PX1, PX2) else None
    pr = d.gable(PX1, PZ, PX2, BZ1, 7, "z", "deepslate_tile_stairs", "deepslate_tile_slab",
                 "calcite" if L >= 3 else stone, overhang=1)
    for z in range(PZ, BZ1):
        for x in range(PX1 + 1, PX2):
            d.set(x, 6, z, "dark_oak_planks") if z > PZ else None
    if L >= 3:                                             # timber-framed porch gable
        for y in range(7, pr):
            d.set(16, y, PZ, "dark_oak_log[axis=y]")
        d.set(15, 7, PZ, "dark_oak_log[axis=x]")
        d.set(17, 7, PZ, "dark_oak_log[axis=x]")
    # back wagon doors
    for x in range(15, 18):
        for y in range(2, 6):
            d.set(x, y, BZ2, "dark_oak_planks")
    d.door(16, 2, BZ2, "south", "dark_oak")
    d.set(16, 4, BZ2, "dark_oak_planks")
    d.set(16, 5, BZ2, "dark_oak_planks")
    # hut in the porch
    d.hut(15, 2, 10, "east")
    d.set(17, 2, 10, "barrel[facing=up,open=false]")
    d.set(16, 5, 11, lantern(True))
    # interior (hand-placed): stepped hay mows against the back wall of each side bay, grain bins (barrels) along
    # the front wall, sacks of threshed grain beside the threshing floor, winnowing corner
    for xa, xb in ((BX1 + 1, 12), (20, BX2 - 1)):
        for x in range(xa, xb + 1):
            if d.get(x, 2, BZ2 - 2).startswith("minecraft:dark_oak_log"):
                continue
            for z, h in ((BZ2 - 1, 3), (BZ2 - 2, 2), (BZ2 - 3, 1)):
                for y in range(2, 2 + h):
                    d.set(x, y, z, "hay_block[axis=x]")
    bins = [BX1 + 2, BX1 + 3, BX2 - 3, BX2 - 2] + ([BX1 + 7, BX1 + 8, BX2 - 8, BX2 - 7] if L >= 2 else [])
    for x in bins:
        d.set(x, 2, BZ1 + 1, "barrel[facing=up,open=false]")
        d.set(x, 3, BZ1 + 1, "barrel[facing=north,open=false]" if x % 2 else "composter[level=8]")
    for x, z in ((13, 16), (13, 17), (19, 16), (19, 17), (19, 18)):
        d.set(x, 2, z, "white_wool")
    d.set(13, 3, 16, "white_wool")
    d.set(19, 2, 19, "composter[level=6]")                 # grain measure
    d.set(13, 2, 19, "grindstone[face=floor,facing=east]")
    d.set(13, 2, 20, "dark_oak_fence")
    d.set(13, 3, 20, "dark_oak_pressure_plate[powered=false]")
    for x in (13, 19):
        if BX1 < x < BX2:
            d.set(x, 7, (BZ1 + BZ2) // 2, lantern(True))
    d.set(16, 7, 18, "chain[axis=y,waterlogged=false]")
    d.set(16, 6, 18, lantern(True))
    # ---- level extras
    if L >= 2:                                             # cart in the forecourt, mounting block
        d.set(20, 2, 7, "oak_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
        d.set(21, 2, 7, "oak_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
        d.set(20, 2, 6, "hay_block[axis=y]")
        d.set(21, 2, 6, "hay_block[axis=y]")
        d.set(19, 2, 6, "dark_oak_fence")
        d.set(12, 2, 11, stair(sst, "east"))
    if L >= 3:                                             # buttresses
        for x in range(BX1 + 2, BX2 - 1, 4):
            if 13 <= x <= 19:
                continue
            for z, f in ((BZ1 - 1, "south"), (BZ2 + 1, "north")):
                for y in range(2, 5):
                    d.set(x, y, z, stone)
                d.set(x, 5, z, stair(sst, f))
        for x in range(10, 23):                            # low forecourt wall with gateposts
            if x in (15, 16, 17):
                continue
            d.set(x, 2, 0, "cobblestone_wall")
        for x in (14, 18):
            d.set(x, 2, 0, stone)
            d.set(x, 3, 0, "stone_brick_slab[type=bottom,waterlogged=false]")
    if L >= 4:                                             # louvred ventilators on the ridge, finials, well
        for x0 in (BX1 + 5, BX2 - 6):
            for x in (x0, x0 + 1):
                d.set(x, ridge, 18, "deepslate_tiles")
                d.set(x, ridge + 1, 18, "dark_oak_fence")
                d.set(x, ridge + 2, 18, "deepslate_tile_slab[type=bottom,waterlogged=false]")
        for x in (BX1, BX2):
            d.set(x, ridge + 1, 18, "stone_brick_wall")
        # well
        for x, z in ((11, 4), (12, 4), (11, 5), (12, 5)):
            d.set(x, 2, z, "cobblestone_wall")
        d.set(11, 3, 4, "oak_fence")
        d.set(12, 3, 5, "oak_fence")
        d.set(11, 4, 4, "oak_slab[type=bottom,waterlogged=false]")
        d.set(12, 4, 4, "oak_slab[type=bottom,waterlogged=false]")
        d.set(11, 4, 5, "oak_slab[type=bottom,waterlogged=false]")
        d.set(12, 4, 5, "oak_slab[type=bottom,waterlogged=false]")
    if L >= 5:                                             # bellcote on the porch, royal banners, garden
        d.set(16, pr + 1, PZ + 1, stone)
        d.set(15, pr + 1, PZ + 1, stone)
        d.set(17, pr + 1, PZ + 1, stone)
        d.set(15, pr + 2, PZ + 1, "stone_brick_wall")
        d.set(17, pr + 2, PZ + 1, "stone_brick_wall")
        d.set(16, pr + 3, PZ + 1, "bell[attachment=ceiling,facing=north,powered=false]")
        for x in (15, 16, 17):
            d.set(x, pr + 4, PZ + 1, "deepslate_tile_slab[type=bottom,waterlogged=false]")
        d.set(16, pr + 4, PZ + 1, "deepslate_tiles")
        d.set(16, pr + 5, PZ + 1, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        for x in (PX1, PX2):
            d.banner(x, 5, PZ - 1, "north", "red")
        for x in range(4, 29):
            if 13 <= x <= 19:
                continue
            if x % 2:
                d.set(x, 2, 11, ("rose_bush[half=lower]", "peony[half=lower]", "lilac[half=lower]")[x % 3])
                d.set(x, 3, 11, ("rose_bush[half=upper]", "peony[half=upper]", "lilac[half=upper]")[x % 3])
        for x in range(3, 30, 6):
            if 13 <= x <= 19:
                continue
            tree(d, x, 25, h=3, leaves="oak_leaves", r=1)
    gr_place_wings(d, g, wonder_path("royalgranary"))
    connect_walls(d)
    return d


def rgw_hearthwood(rel, L):
    """Round stone dovecote with a conical slate roof; potence (ladder post) inside."""
    g = GR["Hearthwood"]
    d = wing_design("Hearthwood", rel, g["wsize"])
    cx = cz = 4
    H = DOVE_H[L]
    body = disc(3.5, cx, cz)
    edge = ring(3.5, cx, cz)
    for x, z in disc(4.5, cx, cz):
        d.set(x, 0, z, "gravel")
    for x, z in body:
        d.set(x, 0, z, "cobblestone")
        for y in range(1, H + 1):
            if (x, z) in edge:
                st = ("smooth_sandstone", "sandstone", "smooth_sandstone", "cut_sandstone")[(x + y * 3 + z * 2) % 4]
                if y == 1:
                    st = "mossy_cobblestone" if (x + z) % 2 else "cobblestone"
                d.set(x, y, z, st)
            else:
                d.set(x, y, z, AIR)
    # string course
    if L >= 3:
        for x, z in edge:
            d.set(x, H - 2, z, "cut_sandstone")
    # nest ledges inside, potence in the middle
    for x, z in edge:
        for y in range(3, H, 2):
            dx, dz = cx - x, cz - z
            if abs(dx) >= abs(dz):
                f = "east" if dx > 0 else "west"
            else:
                f = "south" if dz > 0 else "north"
            nx, nz = x + (1 if f == "east" else -1 if f == "west" else 0), z + (1 if f == "south" else -1 if f == "north" else 0)
            if d.air(nx, y, nz) and (nx, nz) not in ((cx, cz), (cx, cz - 2), (cx, cz - 3), (3, 2)):
                d.set(nx, y, nz, f"spruce_trapdoor[facing={f},half=top,open=false,powered=false,waterlogged=false]")
    for y in range(1, H + 1):
        d.set(cx, y, cz, "dark_oak_log[axis=y]")
    for y in range(1, H):
        d.set(cx, y, cz - 1, "ladder[facing=north,waterlogged=false]")
    d.door(cx, 1, cz - 3, "north", "dark_oak")
    d.set(cx, 3, cz - 3, "dark_oak_planks") if H >= 3 else None
    d.hut(*g["whut"], facing="east")
    # flight holes (pigeon entrances) under the eaves
    for x, z in ((cx, cz + 3), (cx - 3, cz), (cx + 3, cz)):
        d.set(x, H - 1, z, AIR)
    # eaves ring + conical roof
    top = cone(d, cx, cz, 4.0, H + 1, "brick_stairs", "bricks", step=0.75 if L < 3 else 0.6,
               solid="bricks")
    if L >= 4:                                             # glover (pigeon lantern) on the apex
        for x, z in ((cx - 1, cz - 1), (cx + 1, cz - 1), (cx - 1, cz + 1), (cx + 1, cz + 1)):
            d.set(x, top + 1, z, "dark_oak_fence")
        d.fill(cx - 1, top + 2, cz - 1, cx + 1, top + 2, cz + 1, "brick_slab[type=bottom,waterlogged=false]")
        d.set(cx, top + 1, cz, AIR)
        top += 2
    d.set(cx, top + 1, cz, "dark_oak_fence")
    d.set(cx, top + 2, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]" if L >= 5 else "dark_oak_fence")
    connect_walls(d)
    return d


# ----------------------------------------------------------------------------------------------- Cascadia
SILO_H = {1: 8, 2: 11, 3: 14, 4: 17, 5: 20}             # child y of the silo wall top
ELEV_T = {1: 10, 2: 13, 3: 16, 4: 19, 5: 22}            # parent y of the elevator wall top


def core_rg_cascadia(rel, L):
    g = GR["Cascadia"]
    d = Design("Cascadia", rel, g["size"], gy=1, paving="coarse_dirt")
    X1, X2, Z1, Z2 = 11, 19, 12, 20
    T = ELEV_T[L]
    log, pl = "dark_oak_log", "birch_planks"
    # yard, rail siding along the street
    for x in range(d.sx):
        for z in range(d.sz):
            if (x * 5 + z * 3) % 7 == 0:
                d.set(x, 1, z, "grass_block[snowy=false]")
    for x in range(d.sx):
        for z in (1, 2, 3):
            d.set(x, 1, z, "gravel")
        d.set(x, 2, 2, "rail[shape=east_west,waterlogged=false]")
        if x % 2 == 0:
            d.set(x, 1, 2, "spruce_planks")
    # elevator: stone foundation, board walls, dark corner posts and bands
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            d.set(x, 1, z, "spruce_planks")
            edge = x in (X1, X2) or z in (Z1, Z2)
            for y in range(2, T + 1):
                if not edge:
                    d.set(x, y, z, AIR)
                elif y == 2:
                    d.set(x, y, z, ("cobblestone", "mossy_cobblestone", "andesite")[(x + z) % 3])
                elif x in (X1, X2) and z in (Z1, Z2):
                    d.set(x, y, z, f"{log}[axis=y]")
                elif (y - 2) % 5 == 0:
                    d.set(x, y, z, f"{log}[axis={'x' if z in (Z1, Z2) else 'z'}]")
                else:
                    d.set(x, y, z, pl)
    # bin floors inside every 5, ladder (the "leg") up the north-west corner
    for fy in range(7, T, 5):
        d.fill(X1 + 1, fy, Z1 + 1, X2 - 1, fy, Z2 - 1, "spruce_planks")
    for y in range(2, T + 1):
        d.set(X2 - 1, y, Z2 - 1, "ladder[facing=north,waterlogged=false]")
    # every bin floor has its own job (hand-placed; ladder corner (18, 19) and its landing (17, 19) kept clear)
    S_ = STYLE["Cascadia"]
    floors_ = {
        8: [  # distributor floor: the turn-head spout fed from the leg, spout tools, oil and spare buckets
            (15, 8, 16, "hopper[enabled=true,facing=down]"), (15, 9, 16, "hopper[enabled=true,facing=down]"),
            (12, 8, 13, "barrel[facing=up,open=false]"), (12, 9, 13, "barrel[facing=north,open=false]"),
            (13, 8, 13, "barrel[facing=up,open=false]"), (18, 8, 13, "crafting_table"),
            (12, 8, 15, "chest[facing=east,type=single,waterlogged=false]"),
            (12, 8, 19, "grindstone[face=floor,facing=east]"), (14, 8, 19, "cauldron"),
            (13, 7, 18, "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]"),
            (17, 7, 14, "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]"),
            (13, 10, 16, "LAMP"), (17, 10, 16, "LAMP")],
        13: [  # seed-grain bin floor: sacks stacked on pallets along the walls, the weigh scale and tally desk
            (12, 13, 14, "hay_block[axis=y]"), (12, 14, 14, "hay_block[axis=z]"), (12, 13, 15, "hay_block[axis=y]"),
            (12, 13, 17, "white_wool"), (12, 14, 17, "brown_carpet"), (12, 13, 18, "white_wool"),
            (13, 13, 13, "white_wool"), (14, 13, 13, "white_wool"), (13, 14, 13, "white_carpet"),
            (17, 13, 13, "spruce_slab[type=top,waterlogged=false]"), (17, 14, 13, "candle[candles=2,lit=false,waterlogged=false]"),
            (17, 13, 14, "spruce_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]"),
            (18, 13, 15, "lectern[facing=west,has_book=false,powered=false]"),
            (18, 13, 17, "composter[level=6]"), (15, 13, 19, "barrel[facing=up,open=false]"),
            (14, 15, 16, "LAMP"), (16, 15, 17, "LAMP")],
        18: [  # cleaning floor: fanning mill, sieves, screenings bins and the oiling bench under the roof
            (12, 18, 14, "loom[facing=east]"), (12, 18, 16, "stonecutter[facing=east]"),
            (12, 18, 18, "composter[level=3]"), (13, 18, 19, "composter[level=5]"),
            (16, 18, 13, "smithing_table"), (17, 18, 13, "spruce_slab[type=top,waterlogged=false]"),
            (17, 19, 13, "lantern[hanging=false,waterlogged=false]"), (18, 18, 14, "barrel[facing=up,open=false]"),
            (18, 18, 15, "barrel[facing=up,open=false]"), (18, 19, 15, "barrel[facing=west,open=false]"),
            (15, 18, 16, "spruce_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]"),
            (15, 20, 17, "LAMP")],
    }
    for wy, items in floors_.items():
        if wy + 1 > T:
            continue
        for x, y, z, st in items:
            if st == "LAMP":
                piece(d, "lamp", x, y, z, None, S_)
            elif st == "cauldron":
                d.set(x, y, z, "water_cauldron[level=3]")
            else:
                d.set(x, y, z, st if ":" in st or "[" in st or st in ("crafting_table", "smithing_table", "white_wool", "brown_carpet", "white_carpet") else st)
    # small windows
    for y in range(9, T - 1, 5):
        for x in (13, 17):
            d.set(x, y, Z1, "glass_pane")
            d.set(x, y, Z2, "glass_pane")
        for z in (14, 18):
            d.set(X1, y, z, "glass_pane")
            d.set(X2, y, z, "glass_pane")
    # roof (ridge north-south) and the headhouse on top
    ridge = d.gable(X1, Z1, X2, Z2, T + 1, "z", "deepslate_tile_stairs", "deepslate_tile_slab", pl, overhang=1)
    if L >= 2:
        hx1, hx2, hz1, hz2 = 13, 17, 14, 18
        hy = ridge - 2
        for x in range(hx1, hx2 + 1):
            for z in range(hz1, hz2 + 1):
                edge = x in (hx1, hx2) or z in (hz1, hz2)
                for y in range(hy, hy + 4):
                    if edge:
                        d.set(x, y, z, f"{log}[axis=y]" if x in (hx1, hx2) and z in (hz1, hz2) else pl)
                    else:
                        d.set(x, y, z, AIR)
        d.set(15, hy + 2, hz1, "glass_pane")
        d.set(15, hy + 2, hz2, "glass_pane")
        d.gable(hx1, hz1, hx2, hz2, hy + 4, "x", "deepslate_tile_stairs", "deepslate_tile_slab", pl, overhang=1)
    # company sign on the street face
    sy = T - 2
    for x in range(X1 + 1, X2):
        d.set(x, sy, Z1, "stripped_spruce_wood[axis=x]")
        d.set(x, sy - 1, Z1, "stripped_spruce_wood[axis=x]")
    for x, t in ((13, ["CASCADIA"]), (14, ["GRAIN"]), (15, ["CO-OP"]), (16, ["ELEVATOR"]), (17, ["No 1"])):
        d.sign(x, sy, Z1 - 1, "north", t, "dark_oak")
    # drive shed in front: open lean-to with the grain pit and the hut
    SX1, SX2, SZ1 = 12, 18, 6
    for x in range(SX1, SX2 + 1):
        for z in range(SZ1, Z1):
            d.set(x, 1, z, "spruce_planks")
    for x in (SX1, SX2):
        for z in (SZ1, Z1 - 3):
            for y in range(2, 6):
                d.set(x, y, z, "spruce_log[axis=y]")
    for x in range(SX1 - 1, SX2 + 2):
        for i, z in enumerate(range(SZ1 - 1, Z1)):
            y = 5 + (i + 1) // 2
            d.set(x, y, z, stair("dark_oak_stairs", "south") if (i % 2 == 0) else slab("dark_oak_slab", "bottom"))
    for x in range(14, 17):
        for y in range(2, 6):
            d.set(x, y, Z1, AIR)
    d.set(15, 1, 9, "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    d.set(15, 0, 9, "hopper[enabled=true,facing=down]")
    d.hut(SX1 + 1, 2, Z1 - 1, "south")
    d.set(SX2 - 1, 2, Z1 - 1, "composter[level=8]")
    d.set(15, 5, 10, lantern(True)) if d.air(15, 5, 10) else None
    # inside the workfloor: grain cleaner (composter), sacks, scale
    d.set(X1 + 1, 2, Z1 + 1, "barrel[facing=up,open=false]")
    d.set(X1 + 1, 2, Z1 + 2, "barrel[facing=up,open=false]")
    d.set(X1 + 1, 3, Z1 + 1, "barrel[facing=up,open=false]")
    d.set(X2 - 1, 2, Z1 + 1, "hay_block[axis=y]")
    d.set(X2 - 1, 2, Z1 + 2, "hay_block[axis=y]")
    d.set(15, 2, 16, "composter[level=4]")
    d.set(15, 3, 16, "hopper[enabled=true,facing=down]")
    d.set(15, 6, 16, lantern(True))
    # hand-placed workfloor: sacks on the west wall, the agent's desk and ledger, bins on the back wall,
    # barrels and a fanning mill (loom stand-in) on the east wall; ladder corner (18, 19) kept clear
    for z in (15, 16):
        d.set(12, 2, z, "white_wool")
    d.set(12, 3, 15, "white_wool")
    d.set(12, 2, 17, "spruce_slab[type=top,waterlogged=false]")
    d.set(12, 3, 17, "candle[candles=2,lit=false,waterlogged=false]")
    d.set(13, 2, 17, stair("spruce_stairs", "east"))
    d.set(12, 2, 18, "lectern[facing=east,has_book=false,powered=false]")
    d.set(12, 2, 19, "potted_fern")
    for x in (13, 14):
        d.set(x, 2, 19, "barrel[facing=up,open=false]")
        d.set(x, 3, 19, "barrel[facing=north,open=false]")
    d.set(16, 2, 19, "composter[level=7]")
    d.set(18, 2, 15, "barrel[facing=up,open=false]")
    d.set(18, 2, 16, "loom[facing=west]")
    d.set(18, 2, 17, "grindstone[face=floor,facing=west]")
    for x, z in ((14, 16), (16, 16), (15, 15), (15, 17)):
        d.set(x, 1, z, "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    # ---- levels
    if L >= 3:                                             # loading spout over the rail siding
        for i in range(0, 8):
            y = T - 3 - i
            z = Z1 - 1 - i
            if z < 3 or y < 5:
                break
            d.set(15, y, z, "spruce_fence")
        # a grain boxcar on the siding
        for x in range(3, 9):
            d.set(x, 3, 2, "mangrove_planks" if x not in (3, 8) else "dark_oak_planks")
            d.set(x, 4, 2, "mangrove_planks")
            d.set(x, 5, 2, "dark_oak_slab[type=bottom,waterlogged=false]")
            for z in (1, 3):
                d.set(x, 3, z, "mangrove_planks" if x not in (3, 8) else "dark_oak_planks")
                d.set(x, 4, z, "mangrove_planks")
                d.set(x, 5, z, "dark_oak_slab[type=bottom,waterlogged=false]")
        for x in range(3, 9):
            d.set(x, 2, 2, "rail[shape=east_west,waterlogged=false]")
    if L >= 4:                                             # conveyor galleries to the silos
        gy = SILO_H[L] + 1
        for x in (10, 20):
            for y in range(gy, gy + 3):
                d.set(x, y, 16, "spruce_planks" if y != gy + 1 else "glass_pane")
                d.set(x, y, 15, f"{log}[axis=x]" if y == gy else "spruce_planks")
                d.set(x, y, 17, f"{log}[axis=x]" if y == gy else "spruce_planks")
            d.set(x, gy + 3, 16, "dark_oak_slab[type=bottom,waterlogged=false]")
            d.set(x, gy + 3, 15, "dark_oak_slab[type=bottom,waterlogged=false]")
            d.set(x, gy + 3, 17, "dark_oak_slab[type=bottom,waterlogged=false]")
        # scale office shack by the siding
        for x in range(23, 29):
            for z in range(5, 10):
                edge = x in (23, 28) or z in (5, 9)
                d.set(x, 1, z, "spruce_planks")
                for y in range(2, 5):
                    d.set(x, y, z, ("stripped_spruce_log[axis=y]" if x in (23, 28) and z in (5, 9) else pl) if edge else AIR)
        d.door(25, 2, 5, "north", "spruce")
        d.set(27, 3, 5, "glass_pane")
        d.set(23, 3, 7, "glass_pane")
        d.gable(23, 5, 28, 9, 5, "x", "dark_oak_stairs", "dark_oak_slab", pl, overhang=1)
        d.set(24, 2, 8, "lectern[facing=north,has_book=false,powered=false]")
        d.set(27, 2, 8, "barrel[facing=up,open=false]")
        d.set(25, 4, 7, lantern(True))
        d.set(26, 2, 6, "spruce_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
    if L >= 5:                                             # yard dressing: lamps, hay, barrels, firs
        for x, z in ((10, 6), (20, 6)):
            lamppost(d, x, z, post="spruce_fence")
        for x, z in ((2, 7), (3, 7), (2, 8), (27, 25), (28, 25)):
            d.set(x, 2, z, "hay_block[axis=y]")
        d.set(2, 3, 7, "hay_block[axis=x]")
        for x, z in ((4, 26), (26, 27), (15, 27)):
            tree(d, x, z, h=6, log="spruce_log", leaves="spruce_leaves", r=2)
        for x in range(X1 - 1, X2 + 2):
            d.set(x, 2, Z2 + 1, "spruce_fence") if x % 2 else None
    gr_place_wings(d, g, wonder_path("royalgranary"))
    connect_walls(d)
    return d


def rgw_cascadia(rel, L):
    """Round concrete stave silo with iron hoop bands, ladder cage and a conical roof; conveyor stubs at the top."""
    g = GR["Cascadia"]
    d = wing_design("Cascadia", rel, g["wsize"])
    cx = cz = 4
    H = SILO_H[L]
    body = disc(3.5, cx, cz)
    edge = ring(3.5, cx, cz)
    for x, z in disc(4.5, cx, cz):
        d.set(x, 0, z, "gravel")
    for x, z in body:
        d.set(x, 0, z, "cobblestone")
        for y in range(1, H + 1):
            if (x, z) in edge:
                st = "polished_andesite" if y % 4 == 0 else ("andesite" if (x + z + y) % 3 else "tuff")
                if y == 1:
                    st = "mossy_cobblestone" if (x + z) % 2 else "cobblestone"
                d.set(x, y, z, st)
            else:
                d.set(x, y, z, AIR)
    d.door(cx, 1, cz - 3, "north", "spruce")
    d.hut(*g["whut"], facing="east")
    # chute door strip up the front (the classic column of little doors)
    for y in range(3, H, 2):
        d.set(cx, y, cz - 3, "spruce_planks")
    for y in range(3, H + 1):
        d.set(cx - 1, y, cz - 4, "ladder[facing=north,waterlogged=false]")
    # interior: a grain heap and a lantern
    d.set(cx, 1, cz + 1, "hay_block[axis=y]")
    d.set(cx + 1, 1, cz + 1, "hay_block[axis=y]")
    d.set(cx, H, cz, "spruce_planks")
    d.set(cx, H - 1, cz, lantern(True))
    top = cone(d, cx, cz, 3.6, H + 1, "deepslate_tile_stairs", "deepslate_tiles", step=0.9, solid="deepslate_tiles")
    d.set(cx, top + 1, cz, "spruce_fence")
    d.set(cx, top + 2, cz, lantern() if L >= 3 else "spruce_fence")
    if L >= 4:                                             # conveyor stubs both sides (one meets the elevator gallery)
        for x in (0, 8):
            for y in range(H, H + 3):
                for z in (3, 4, 5):
                    d.set(x, y, z, "spruce_planks" if not (z == 4 and y == H + 1) else "glass_pane")
                d.set(x, H, 3, "dark_oak_log[axis=x]")
                d.set(x, H, 5, "dark_oak_log[axis=x]")
            for z in (3, 4, 5):
                d.set(x, H + 3, z, "dark_oak_slab[type=bottom,waterlogged=false]")
        for x in (1, 7):
            for y in range(H, H + 3):
                for z in (3, 4, 5):
                    if d.air(x, y, z):
                        d.set(x, y, z, "spruce_planks")
            for z in (3, 4, 5):
                if d.air(x, H + 3, z):
                    d.set(x, H + 3, z, "dark_oak_slab[type=bottom,waterlogged=false]")
    connect_walls(d)
    return d


# ----------------------------------------------------------------------------------------------- Neoterra
NSILO_H = {1: 5, 2: 8, 3: 11, 4: 14, 5: 17}


def core_rg_neoterra(rel, L):
    g = GR["Neoterra"]
    d = Design("Neoterra", rel, g["size"], gy=1, paving="grass_block[snowy=false]")
    SOLIDB = "structurize:blocksolidsubstitution"
    # plaza along the street and the approach
    for x in range(d.sx):
        for z in range(0, 5):
            d.set(x, 1, z, "smooth_stone" if (x + z) % 4 else "light_gray_concrete")
    for x in range(13, 20):
        for z in range(0, 13):
            d.set(x, 1, z, "white_concrete" if x in (13, 19) else "smooth_stone")
    # ---- the mound (grassed hill over the vault)
    mx, mz, rx, rz = 16, 22, 10, 8.5
    Hm = 8 if L == 1 else 9
    hmap = {}
    for x in range(d.sx):
        for z in range(d.sz):
            t = 1 - ((x - mx) / rx) ** 2 - ((z - mz) / rz) ** 2
            if t > 0:
                h = int(round(Hm * (t ** 0.6)))
                if h > 0:
                    hmap[(x, z)] = h
    for (x, z), h in hmap.items():
        for y in range(2, 1 + h):
            d.set(x, y, z, SOLIDB)
        d.set(x, 1 + h, z, "grass_block[snowy=false]" if h < Hm - 1 or L < 3 else "moss_block")
    # ---- vault chamber inside the mound
    VX1, VX2, VZ1, VZ2 = 12, 20, 19, 27
    for x in range(VX1, VX2 + 1):
        for z in range(VZ1, VZ2 + 1):
            d.set(x, 1, z, "polished_diorite" if (x + z) % 2 else "packed_ice")
            for y in range(2, 6):
                d.set(x, y, z, "white_concrete" if x in (VX1, VX2) or z in (VZ1, VZ2) else AIR)
            d.set(x, 6, z, "light_gray_concrete")
    for x in range(VX1 + 2, VX2 - 1, 3):
        for z in (VZ1 + 2, VZ1 + 5):
            d.set(x, 5, z, "sea_lantern")
    # seed shelving: aisles of barrels 2 high along x, with a central aisle
    for z in (VZ1 + 2, VZ1 + 4, VZ1 + 6):
        for x in range(VX1 + 1, VX2):
            if x == 16:
                continue
            d.set(x, 2, z, "barrel[facing=up,open=false]")
            d.set(x, 3, z, "barrel[facing=north,open=false]" if x % 2 else "decorated_pot[cracked=false,facing=north,waterlogged=false]")
    # ---- corridor from the portal
    for z in range(6, VZ1):
        for x in range(14, 19):
            edge = x in (14, 18)
            d.set(x, 1, z, "polished_andesite" if not edge else "white_concrete")
            for y in range(2, 5):
                d.set(x, y, z, "white_concrete" if edge else AIR)
            d.set(x, 5, z, "light_gray_concrete")
            if not edge and z > 13:
                pass
        if z % 2 == 0:
            d.set(16, 5, z, "sea_lantern")
    for y in range(2, 4):
        d.set(16, y, VZ1, AIR)
    d.set(16, 2, VZ1, "iron_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
    d.set(16, 3, VZ1, "iron_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
    # ---- the portal wedge
    PX1, PX2, PZ1, PZ2 = 13, 19, 5, 13
    for z in range(PZ1, PZ2 + 1):
        ytop = 12 - (z - PZ1)
        for x in range(PX1, PX2 + 1):
            for y in range(2, ytop + 1):
                inside = 15 <= x <= 17 and y <= 4 and z > PZ1
                if inside:
                    continue
                if 15 <= x <= 17 and 2 <= y <= 4:
                    continue
                d.set(x, y, z, "polished_andesite" if x in (PX1, PX2) or z == PZ1 or y == ytop else SOLIDB)
    for z in range(PZ1, PZ2 + 1):                         # smooth sloping top
        ytop = 12 - (z - PZ1)
        for x in range(PX1, PX2 + 1):
            d.set(x, ytop + 1, z, stair("polished_andesite_stairs", "north"))
    # the glowing art on the front face and roof (diagonal light strips)
    for z in range(PZ1, PZ2 + 1):
        ytop = 12 - (z - PZ1)
        for x in range(PX1 + 1, PX2):
            if (x + z) % 3 == 0:
                d.set(x, ytop, z, "sea_lantern" if L >= 2 else "cyan_concrete")
            elif L >= 3:
                d.set(x, ytop, z, "prismarine_bricks" if (x + z) % 3 == 1 else "light_blue_stained_glass")
    for y in range(6, 13):
        for x in range(PX1 + 1, PX2):
            if (x + y) % 3 == 0:
                d.set(x, y, PZ1, "sea_lantern" if L >= 2 else "cyan_concrete")
            elif L >= 4 and (x + y) % 3 == 1:
                d.set(x, y, PZ1, "light_blue_stained_glass")
    # entrance
    for x in range(15, 18):
        for y in range(2, 5):
            d.set(x, y, PZ1, "glass_pane" if x != 16 else AIR)
        d.set(x, 5, PZ1, "light_gray_concrete")
    d.set(16, 2, PZ1, "iron_door[facing=north,half=lower,hinge=left,open=false,powered=false]")
    d.set(16, 3, PZ1, "iron_door[facing=north,half=upper,hinge=left,open=false,powered=false]")
    d.set(16, 4, PZ1, "glass_pane")
    d.hut(15, 2, PZ1 + 2, "east")
    d.sign(13, 3, PZ1 - 1, "north", ["NEOTERRA", "SEED VAULT"], "birch", glow=True, color="cyan")
    # ---- research pavilion (L3+) and greenhouse (L4+)
    if L >= 3:
        x1, x2, z1, z2 = 23, 31, 9, 16
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                d.set(x, 1, z, "smooth_stone")
                edge = x in (x1, x2) or z in (z1, z2)
                for y in range(2, 6):
                    if edge:
                        corner = x in (x1, x2) and z in (z1, z2)
                        d.set(x, y, z, "white_concrete" if corner or y == 5 else "light_blue_stained_glass_pane" if L >= 4 else "glass_pane")
                    else:
                        d.set(x, y, z, AIR)
        d.flat(x1 - 1, z1 - 1, x2 + 1, z2 + 1, 6, "smooth_quartz")
        for x in range(x1 + 1, x2, 2):
            for z in range(z1 + 1, z2, 2):
                d.set(x, 7, z, "daylight_detector[inverted=false,power=0]")
        d.set(27, 2, z1, AIR)
        d.set(27, 3, z1, AIR)
        d.door(27, 2, z1, "north", "birch")
        for x in range(x1 + 1, x2):
            d.set(x, 2, z2 - 1, "smooth_quartz_slab[type=top,waterlogged=false]") if x % 3 else None
        d.set(x1 + 2, 2, z2 - 2, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
        d.set(x2 - 1, 2, z1 + 1, "potted_bamboo")
        for x in range(x1 + 2, x2 - 1, 3):
            d.set(x, 5, (z1 + z2) // 2, "sea_lantern")
        for x in range(x1 + 1, x2):
            if x % 3 == 0:
                d.set(x, 3, z2 - 1, "potted_fern")
        for x, z, bush in ((22, 8, "flowering_azalea"), (32, 8, "azalea"), (22, 17, "azalea"),
                           (32, 17, "flowering_azalea")):          # planters at the canopy corners
            d.set(x, 1, z, "moss_block")
            d.set(x, 2, z, bush)
    if L >= 4:
        x1, x2, z1, z2 = 1, 9, 9, 16
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                d.set(x, 1, z, "moss_block" if x not in (x1, x2, 5) and z not in (z1, z2) else "smooth_stone")
                edge = x in (x1, x2) or z in (z1, z2)
                for y in range(2, 5):
                    d.set(x, y, z, ("white_concrete" if x in (x1, x2) and z in (z1, z2) else "glass_pane") if edge else AIR)
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                d.set(x, 5, z, "glass" if x not in (x1, x2) and z not in (z1, z2) else "white_concrete")
        d.set(5, 2, z1, AIR)
        d.set(5, 3, z1, AIR)
        d.door(5, 2, z1, "north", "birch")
        # trial beds either side of the centre walk: one crop per bed, chosen by hand
        for (xa, xb), crop in (((x1 + 1, 4), "wheat[age=7]"), ((6, x2 - 1), "carrots[age=5]")):
            for x in range(xa, xb + 1):
                for z in (z1 + 1, z1 + 2, z1 + 4, z1 + 5):
                    d.set(x, 1, z, "farmland[moisture=7]")
                    d.set(x, 2, z, crop if z < z1 + 3 else ("potatoes[age=7]" if crop.startswith("wheat") else "beetroots[age=3]"))
        for x, z in ((3, 12), (7, 12), (3, 15), (7, 15)):   # grow lights over the walks
            d.set(x, 5, z, "sea_lantern")
        d.set(2, 2, 15, "water_cauldron[level=3]")
        d.set(8, 2, 15, "composter[level=4]")
        d.set(2, 2, 12, "barrel[facing=up,open=false]")
    if L >= 5:                                             # reflecting pools and flag poles on the plaza
        for x0 in (9, 20):
            for x in range(x0, x0 + 4):
                for z in (6, 7, 8):
                    d.set(x, 1, z, WATER)
                d.set(x, 1, 5, "white_concrete")
                d.set(x, 1, 9, "white_concrete")
        for x in (11, 21):
            for y in range(2, 9):
                d.set(x, y, 2, "iron_bars")
            d.set(x, 9, 2, "sea_lantern")
        for x in range(10, 23, 3):
            d.set(x, 1, 0, "sea_lantern")
    gr_place_wings(d, g, wonder_path("royalgranary"))
    connect_walls(d)
    return d


def rgw_neoterra(rel, L):
    """White concrete silo with cyan bands, a vertical window strip and (later) a glass observation crown."""
    g = GR["Neoterra"]
    d = wing_design("Neoterra", rel, g["wsize"])
    cx = cz = 3
    H = NSILO_H[L]
    body = disc(3.4, cx, cz)
    edge = ring(3.4, cx, cz)
    for x, z in body:
        d.set(x, 0, z, "smooth_stone")
        for y in range(1, H + 1):
            if (x, z) in edge:
                st = "orange_concrete" if y % 4 == 0 else "white_concrete"
                if y == 1:
                    st = "light_gray_concrete"
                d.set(x, y, z, st)
            else:
                d.set(x, y, z, AIR)
    for y in range(2, H):
        d.set(cx, y, cz + 3, "light_blue_stained_glass_pane" if L >= 3 else "glass_pane")
    d.set(cx, 1, 0, AIR)
    d.set(cx, 2, 0, AIR)
    d.door(cx, 1, 0, "north", "birch")
    d.hut(*g["whut"], facing="east")
    d.set(cx, H, cz, "sea_lantern")
    for x, z in body:
        if (x, z) not in edge:
            d.set(x, H, z, "white_concrete")
    d.set(cx, H, cz, "sea_lantern")
    top = H + 1
    if L >= 3:                                             # glass observation ring with a flat cap
        for x, z in edge:
            d.set(x, top, z, "light_blue_stained_glass")
            d.set(x, top + 1, z, "light_blue_stained_glass" if L >= 4 else "white_concrete")
        for x, z in body:
            d.set(x, top + 2, z, "smooth_quartz")
        top += 3
    else:
        for x, z in edge:
            d.set(x, top, z, "smooth_quartz_slab[type=bottom,waterlogged=false]")
    if L >= 5:
        for x, z in disc(2.2, cx, cz):
            d.set(x, top, z, "light_blue_stained_glass")
        d.set(cx, top + 1, cz, "sea_lantern")
        d.set(cx, top + 2, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    connect_walls(d)
    return d


@design("royalgranary")
def royalgranary(pack, rel, L):
    return undercover({"Hearthwood": rg_hearthwood, "Cascadia": rg_cascadia, "Neoterra": rg_neoterra}[pack](rel, L))


@design("royalgranarywing")
def royalgranarywing(pack, rel, L):
    return {"Hearthwood": rgw_hearthwood, "Cascadia": rgw_cascadia, "Neoterra": rgw_neoterra}[pack](rel, L)


# =============================================================================================================
#                      GROWTH: the cores above are pasted into a larger plot and grow into complexes
# =============================================================================================================
SOLIDB = "structurize:blocksolidsubstitution"
DIRS = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}
OPPD = {"north": "south", "south": "north", "east": "west", "west": "east"}


def paste(big, small, ox, oz):
    """Copy a finished-drawing (not finished) small Design into `big` at offset (ox, oz), with hut, children, tags."""
    for x, y, z, s in small.bp.blocks():
        if s == AIR:
            continue
        big.bp.set(x + ox, y, z + oz, s, small.bp.tile_entities.get((x, y, z)))
    for (x, y, z), ns in small.tags.items():
        big.tags.setdefault((x + ox, y, z + oz), []).extend(ns)
    hx, hy, hz = small.hut_pos
    big.hut_pos = (hx + ox, hy, hz + oz)
    big.child_positions = [(x + ox, y, z + oz, p) for (x, y, z, p) in small.child_positions]
    big.placed = small.placed


# ------------------------------------------------------------------------------------------- building kit
# palette variants per pack (each building of a complex takes another one)
PALS = {
    "Hearthwood": [
        dict(wall="calcite", post="stripped_dark_oak_log", roofst="deepslate_tile_stairs", roofsl="deepslate_tile_slab",
             end="calcite", trap="crimson_trapdoor", wood="dark_oak"),
        dict(wall="smooth_sandstone", post="stripped_oak_log", base="sandstone", roofst="dark_prismarine_stairs",
             roofsl="dark_prismarine_slab", end="smooth_sandstone", trap="warped_trapdoor", wood="oak", beam="stripped_oak_log"),
        dict(wall="bricks", post="stripped_dark_oak_log", base="stone_bricks", roofst="mud_brick_stairs",
             roofsl="mud_brick_slab", end="bricks", trap="spruce_trapdoor", wood="spruce", chim="stone_bricks",
             chimcap="stone_brick_slab"),
        dict(wall="yellow_terracotta", post="stripped_dark_oak_log", roofst="brick_stairs", roofsl="brick_slab",
             end="yellow_terracotta", trap="dark_oak_trapdoor", wood="dark_oak"),
        dict(wall="white_terracotta", post="stripped_oak_log", base="cobblestone", roofst="granite_stairs",
             roofsl="granite_slab", end="white_terracotta", trap="crimson_trapdoor", wood="oak", beam="stripped_oak_log"),
        dict(wall="pink_terracotta", post="stripped_dark_oak_log", roofst="spruce_stairs", roofsl="spruce_slab",
             end="pink_terracotta", trap="oak_trapdoor", wood="dark_oak"),
        dict(wall="light_blue_terracotta", post="stripped_dark_oak_log", roofst="deepslate_tile_stairs",
             roofsl="deepslate_tile_slab", end="light_blue_terracotta", trap="spruce_trapdoor", wood="spruce"),
    ],
    "Cascadia": [
        dict(wall="spruce_log", post="stripped_spruce_log", roofst="cobbled_deepslate_stairs",
             roofsl="cobbled_deepslate_slab", end="spruce_planks", trap="spruce_trapdoor"),
        dict(wall="stripped_spruce_log", post="dark_oak_log", roofst="mangrove_stairs", roofsl="mangrove_slab",
             end="dark_oak_planks", trap="dark_oak_trapdoor"),
        dict(wall="dark_oak_log", post="stripped_dark_oak_log", roofst="dark_prismarine_stairs",
             roofsl="dark_prismarine_slab", end="dark_oak_planks", trap="mangrove_trapdoor"),
        dict(wall="stripped_birch_log", post="spruce_log", roofst="spruce_stairs", roofsl="spruce_slab",
             end="birch_planks", trap="spruce_trapdoor"),
        dict(wall="stripped_mangrove_log", post="spruce_log", roofst="deepslate_tile_stairs",
             roofsl="deepslate_tile_slab", end="mangrove_planks", trap="dark_oak_trapdoor"),
        dict(wall="spruce_log", post="dark_oak_log", roofst="warped_stairs", roofsl="warped_slab",
             end="spruce_planks", trap="crimson_trapdoor"),
    ],
    "Neoterra": [
        dict(wall="white_concrete", post="light_gray_concrete", band="cyan_terracotta"),
        dict(wall="light_gray_concrete", post="gray_concrete", band="orange_concrete", parapet="light_gray_concrete"),
        dict(wall="white_terracotta", post="polished_blackstone", band="yellow_concrete", parapet="polished_blackstone"),
        dict(wall="quartz_block", post="polished_deepslate", band="lime_concrete", parapet="smooth_quartz"),
        dict(wall="birch_planks", post="white_concrete", band="cyan_concrete"),
        dict(wall="cyan_terracotta", post="white_concrete", band="magenta_concrete", parapet="white_concrete"),
        dict(wall="gray_concrete", post="white_concrete", band="orange_terracotta", parapet="smooth_quartz"),
    ],
}


STYLE = {
    "Hearthwood": dict(floor="oak_planks", wall="calcite", post="stripped_dark_oak_log", base="stone_bricks",
                       beam="stripped_dark_oak_log", roofst="deepslate_tile_stairs", roofsl="deepslate_tile_slab",
                       end="calcite", wood="dark_oak", trap="dark_oak_trapdoor", chim="bricks",
                       chimcap="brick_slab", rug=("red_carpet", "orange_carpet"), path="gravel", lamp="lantern",
                       counter="dark_oak_slab", flowers=("poppy", "oxeye_daisy", "cornflower", "allium")),
    "Cascadia": dict(floor="spruce_planks", wall="spruce_log", post="stripped_spruce_log", base="cobblestone",
                     beam="spruce_log", roofst="dark_oak_stairs", roofsl="dark_oak_slab", end="spruce_planks",
                     wood="spruce", trap="spruce_trapdoor", chim="cobblestone", chimcap="cobblestone_slab",
                     rug=("brown_carpet", "green_carpet"), path="coarse_dirt", lamp="lantern",
                     counter="spruce_slab", flowers=("fern", "blue_orchid", "lily_of_the_valley", "dandelion")),
    "Neoterra": dict(floor="polished_diorite", wall="white_concrete", post="light_gray_concrete",
                     base="light_gray_concrete", beam="light_gray_concrete", roofst="smooth_quartz_stairs",
                     roofsl="smooth_quartz_slab", end="white_concrete", wood="birch", trap="birch_trapdoor",
                     chim=None, chimcap=None, rug=("cyan_carpet", "light_gray_carpet"), path="smooth_stone",
                     lamp="sea_lantern", counter="smooth_quartz_slab",
                     flowers=("azure_bluet", "white_tulip", "allium", "lily_of_the_valley")),
}


def _shelf(face):
    occ = ["true", "false", "true", "true", "false", "true"]
    return (f"chiseled_bookshelf[facing={face}," + ",".join(f"slot_{i}_occupied={o}" for i, o in enumerate(occ)) + "]")


def _pot(face="north"):
    return f"decorated_pot[cracked=false,facing={face},waterlogged=false]"


def piece(d, kind, x, y, z, arg, S):
    """Draw ONE furnishing piece at (x, y, z). arg = facing (into the room) for oriented pieces, the backrest
    side for chairs, a block state for '=' and tops, a colour for carpets/banners."""
    wood = S["wood"]
    slabtop = f"{S['counter']}[type=top,waterlogged=false]"
    if kind == "=":
        d.set(x, y, z, arg)
    elif kind == "bed":                                    # head here, foot one cell toward `arg`
        col = {"Hearthwood": "red", "Cascadia": "brown", "Neoterra": "cyan"}[d.pack]
        dx, dz = DIRS[arg]
        d.set(x + dx, y, z + dz, f"{col}_bed[facing={OPPD[arg]},occupied=false,part=foot]")
        d.set(x, y, z, f"{col}_bed[facing={OPPD[arg]},occupied=false,part=head]")
    elif kind == "chair":
        d.set(x, y, z, stair(f"{wood}_stairs", arg))
    elif kind == "table":                                  # post table, arg = what stands on it (or None)
        d.set(x, y, z, f"{wood}_fence")
        d.set(x, y + 1, z, arg or f"{wood}_pressure_plate[powered=false]")
    elif kind == "counter":
        d.set(x, y, z, slabtop)
        if arg:
            d.set(x, y + 1, z, arg)
    elif kind == "nightstand":
        d.set(x, y, z, slabtop)
        d.set(x, y + 1, z, "candle[candles=1,lit=false,waterlogged=false]" if arg == "candle" else lantern())
    elif kind == "shelf":                                  # two-high chiseled bookcase
        d.set(x, y, z, _shelf(arg))
        d.set(x, y + 1, z, _shelf(arg))
    elif kind == "books":
        d.set(x, y, z, "bookshelf")
        d.set(x, y + 1, z, "bookshelf")
    elif kind == "barrel":
        d.set(x, y, z, "barrel[facing=up,open=false]")
    elif kind == "barrels":
        d.set(x, y, z, "barrel[facing=up,open=false]")
        d.set(x, y + 1, z, f"barrel[facing={arg},open=false]")
    elif kind == "keg":                                    # cask on its side on a stand, arg = axis direction
        d.set(x, y, z, f"barrel[facing={arg},open=false]")
    elif kind == "sacks":
        d.set(x, y, z, "white_wool")
        d.set(x, y + 1, z, arg or "brown_carpet")
    elif kind == "hay":
        d.set(x, y, z, "hay_block[axis=y]")
        if arg:
            d.set(x, y + 1, z, "hay_block[axis=x]")
    elif kind == "lectern":
        d.set(x, y, z, f"lectern[facing={arg},has_book=false,powered=false]")
    elif kind in ("crafting_table", "cartography_table", "fletching_table", "smithing_table"):
        d.set(x, y, z, kind)
    elif kind in ("furnace", "smoker", "blast_furnace"):
        d.set(x, y, z, f"{kind}[facing={arg},lit=false]")
    elif kind == "cauldron":
        d.set(x, y, z, "water_cauldron[level=3]")
    elif kind == "brewing":
        d.set(x, y, z, slabtop)
        d.set(x, y + 1, z, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
    elif kind == "loom":
        d.set(x, y, z, f"loom[facing={arg}]")
    elif kind == "stonecutter":
        d.set(x, y, z, f"stonecutter[facing={arg}]")
    elif kind == "grindstone":
        d.set(x, y, z, f"grindstone[face=floor,facing={arg}]")
    elif kind == "anvil":
        d.set(x, y, z, f"anvil[facing={arg}]")
    elif kind == "carpet":
        d.set(x, y, z, f"{arg}_carpet")
    elif kind == "banner":
        d.set(x, y, z, f"{arg[1]}_wall_banner[facing={arg[0]}]")
    elif kind == "pot":
        d.set(x, y, z, _pot(arg or "north"))
    elif kind == "candle":
        d.set(x, y, z, f"candle[candles={arg or 2},lit=false,waterlogged=false]")
    elif kind == "lamp":                                   # lantern hung on a chain from the ceiling above
        yy = y + 1
        while d.air(x, yy, z) and yy < y + 6:
            yy += 1
        for k in range(y + 1, yy):
            d.set(x, k, z, "chain[axis=y,waterlogged=false]")
        d.set(x, y, z, lantern(True))
    elif kind == "torch":
        d.wall_torch(x, y, z, arg)
    elif kind == "sign":
        d.sign(x, y, z, arg[0], arg[1], S["wood"] if d.pack != "Neoterra" else "birch",
               glow=d.pack == "Neoterra", color="cyan" if d.pack == "Neoterra" else "black")
    elif kind == "box":                                    # window box under a window: trapdoor sill + flower
        d.set(x, y, z, f"{S['trap']}[facing={arg[0]},half=top,open=false,powered=false,waterlogged=false]")
        d.set(x, y + 1, z, f"potted_{arg[1]}")
    elif kind == "shutter":
        d.set(x, y, z, f"{S['trap']}[facing={arg},half=bottom,open=true,powered=false,waterlogged=false]")
        d.set(x, y + 1, z, f"{S['trap']}[facing={arg},half=bottom,open=true,powered=false,waterlogged=false]")
    elif kind == "flower":
        d.set(x, y - 1, z, "grass_block[snowy=false]" if d.pack != "Neoterra" else "moss_block")
        if arg.endswith("_bush") or arg in ("peony", "lilac"):
            d.set(x, y, z, f"{arg}[half=lower]")
            d.set(x, y + 1, z, f"{arg}[half=upper]")
        else:
            d.set(x, y, z, arg)
    else:
        raise ValueError(kind)


def F(d, b, items):
    """Place a hand-written list of pieces for building `b` (the dict building() returns). Each item is
    (dx, dy, dz, kind, arg) relative to the building's north-west corner and ground walk level."""
    S = b["S"]
    for dx, dy, dz, kind, arg in items:
        piece(d, kind, b["x1"] + dx, b["y0"] + dy, b["z1"] + dz, arg, S)


# Plan symbols (hand-drawn room plans, one character per interior cell, rows north->south, columns west->east).
# '.' / ' ' = keep free.  Oriented pieces carry their facing in the symbol; the per-room `face` dict gives the
# facing of workstations (K smoker, F furnace, G grindstone, V stonecutter, Q lectern, A anvil, M loom).
LEGEND = {
    "b": ("barrel", None), "B": ("barrels", "north"), "s": ("sacks", None), "h": ("hay", True), "H": ("hay", None),
    "k": ("crafting_table", None), "m": ("cartography_table", None), "f": ("fletching_table", None),
    "w": ("smithing_table", None), "c": ("counter", None),
    "d": ("counter", "candle[candles=3,lit=false,waterlogged=false]"),
    "e": ("counter", "decorated_pot[cracked=false,facing=north,waterlogged=false]"),
    "g": ("counter", "potted_red_tulip"), "i": ("counter", "potted_fern"),
    "n": ("nightstand", None), "j": ("nightstand", "candle"),
    "p": ("=", "potted_fern"), "a": ("=", "potted_azalea_bush"), "z": ("=", "potted_bamboo"),
    "u": ("=", "potted_red_tulip"), "P": ("pot", "north"), "C": ("cauldron", None), "r": ("brewing", None),
    "T": ("table", None), "t": ("table", "candle[candles=2,lit=false,waterlogged=false]"),
    "^": ("bed", "north"), "v": ("bed", "south"), "<": ("bed", "west"), ">": ("bed", "east"),
    "1": ("chair", "north"), "2": ("chair", "east"), "3": ("chair", "south"), "4": ("chair", "west"),
    "5": ("shelf", "north"), "6": ("shelf", "east"), "7": ("shelf", "south"), "8": ("shelf", "west"),
    "9": ("books", None), "x": ("keg", "east"), "y": ("keg", "north"),
    "X": ("=", "spruce_log[axis=x]"), "Z": ("=", "stripped_spruce_log[axis=x]"),
    "E": ("=", "oak_fence"), "W": ("=", "white_wool"), "Y": ("=", "yellow_wool"), "O": ("=", "orange_wool"), "J": ("=", "jukebox[has_record=false]"),
}
FACED = {"U": "blast_furnace", "K": "smoker", "F": "furnace", "G": "grindstone", "V": "stonecutter", "Q": "lectern", "A": "anvil",
         "M": "loom"}


def plan(d, b, storey, rows, face=None, lamps=(), rugs=None):
    """Furnish one storey of building b from a hand-drawn plan. rows must cover the interior exactly.
    'R' / 'o' = carpet in the pack's two rug colours, '@' = carpet with a hanging lamp above, 'l' = hanging lamp
    over free floor."""
    S = b["S"]
    yb = b["y0"] + 5 * storey
    W = b["x2"] - b["x1"] - 1
    assert len(rows) == b["z2"] - b["z1"] - 1, (b["x1"], b["z1"], storey, len(rows))
    rc = rugs or S["rug"]
    for r, row in enumerate(rows):
        assert len(row) == W, (b["x1"], b["z1"], storey, r, row)
        z = b["z1"] + 1 + r
        for c, ch in enumerate(row):
            x = b["x1"] + 1 + c
            if ch in ". ":
                continue
            if ch in "Ro@":
                d.set(x, yb, z, rc[1] if ch == "o" else rc[0])
                if ch == "@":
                    piece(d, "lamp", x, yb + 3, z, None, S)
            elif ch == "l":
                piece(d, "lamp", x, yb + 3, z, None, S)
            elif ch in FACED:
                piece(d, FACED[ch], x, yb, z, (face or {}).get(ch, "north"), S)
            else:
                k, a = LEGEND[ch]
                piece(d, k, x, yb, z, a, S)


def building(d, x1, z1, x2, z2, storeys, door="south", doorpos=None, ladder=None, hearth=None, y0=2,
             roof="gable", axis=None, pal=0):
    """Shell of a building in the pack's style: floors, walls, window openings, door, ladder (explicit cell and
    facing), fireplace with chimney stack (explicit hearth cell and the direction it opens to) and roof.
    Furniture and outside dressing are NOT placed here - every building gets its own hand-written list (F)."""
    S = dict(STYLE[d.pack])
    S.update(PALS[d.pack][pal % len(PALS[d.pack])])
    S.setdefault("band", "light_gray_concrete")
    pk = d.pack
    n = storeys
    SH = 5
    lx, lz = x2 - x1, z2 - z1
    axis = axis or ("x" if lx >= lz else "z")
    if door in ("north", "south"):
        dpx = doorpos if doorpos is not None else (x1 + x2) // 2
        dcell = (dpx, z1 if door == "north" else z2)
    else:
        dpz = doorpos if doorpos is not None else (z1 + z2) // 2
        dcell = (x1 if door == "west" else x2, dpz)
    chim = None
    if hearth:
        hx, hz, hf = hearth
        bx, bz = DIRS[OPPD[hf]]
        chim = (hx + bx, hz + bz)
    windows = []
    for s in range(n):
        yb = y0 + s * SH
        d.fill(x1, yb - 1, z1, x2, yb - 1, z2, S["floor"])
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                edge = x in (x1, x2) or z in (z1, z2)
                corner = x in (x1, x2) and z in (z1, z2)
                for y in range(yb, yb + 4):
                    if not edge:
                        d.set(x, y, z, AIR)
                        continue
                    along = (x - x1) if z in (z1, z2) else (z - z1)
                    if pk == "Hearthwood":
                        st = f"{S['post']}[axis=y]" if (corner or along % 4 == 0) else \
                            (S["base"] if s == 0 and y == yb else S["wall"])
                    elif pk == "Cascadia":
                        st = f"{S['post']}[axis=y]" if corner else \
                            f"{S['wall']}[axis={'x' if z in (z1, z2) else 'z'}]"
                    else:
                        st = S["post"] if corner else (S["wall"] if y != yb + 3 else S["band"])
                    d.set(x, y, z, st)
        if s > 0:
            for x in range(x1, x2 + 1):
                for z in (z1, z2):
                    d.set(x, yb - 1, z, f"{S['beam']}[axis=x]" if pk != "Neoterra" else S["band"])
            for z in range(z1, z2 + 1):
                for x in (x1, x2):
                    d.set(x, yb - 1, z, f"{S['beam']}[axis=z]" if pk != "Neoterra" else S["band"])
        elif pk == "Cascadia":
            for x in range(x1, x2 + 1):
                for z in range(z1, z2 + 1):
                    if x in (x1, x2) or z in (z1, z2):
                        d.set(x, yb - 1, z, ("cobblestone", "mossy_cobblestone", "andesite")[(x + z) % 3])
        # window openings: every third wall cell (Neoterra: ribbon glazing between fins)
        for cells, out in (([(x, z1) for x in range(x1, x2 + 1)], "north"), ([(x, z2) for x in range(x1, x2 + 1)], "south"),
                           ([(x1, z) for z in range(z1, z2 + 1)], "west"), ([(x2, z) for z in range(z1, z2 + 1)], "east")):
            for i, (x, z) in enumerate(cells):
                if i < 1 or i > len(cells) - 2 or (x, z) == chim:
                    continue
                if pk == "Neoterra":
                    if i % 4 == 0:
                        continue
                    for y in (yb + 1, yb + 2):
                        d.set(x, y, z, "light_gray_stained_glass_pane" if s % 2 else "glass_pane")
                    continue
                if i % 3 != 2 or (s == 0 and abs(x - dcell[0]) + abs(z - dcell[1]) <= 1):
                    continue
                d.set(x, yb + 1, z, "glass_pane")
                d.set(x, yb + 2, z, "glass_pane")
                windows.append((x, yb, z, out))
    top = y0 + n * SH - 1
    if n > 1:
        lx_, lz_, lf = ladder
        for y in range(y0, y0 + (n - 1) * SH):
            d.set(lx_, y, lz_, f"ladder[facing={lf},waterlogged=false]")
    if hearth:
        hx, hz, hf = hearth
        d.set(hx, y0, hz, f"campfire[facing={hf},lit=true,signal_fire=false,waterlogged=false]")
        for y in range(y0 + 1, y0 + 4):
            d.set(hx, y, hz, S["chim"])
        side = ((1, 0), (-1, 0)) if hf in ("north", "south") else ((0, 1), (0, -1))
        for sx_, sz_ in side:                               # hearth cheeks with a mantel shelf
            d.set(hx + sx_, y0, hz + sz_, S["chim"])
            d.set(hx + sx_, y0 + 1, hz + sz_, f"{S['chimcap']}[type=bottom,waterlogged=false]")
    d.set(dcell[0], y0, dcell[1], AIR)
    d.set(dcell[0], y0 + 1, dcell[1], AIR)
    d.door(dcell[0], y0, dcell[1], door, S["wood"] if pk != "Neoterra" else "birch")
    ox, oz = DIRS[door]
    if d.bp.inside(dcell[0] + ox, 1, dcell[1] + oz):
        d.set(dcell[0] + ox, 1, dcell[1] + oz, S["path"])
    info = dict(x1=x1, z1=z1, x2=x2, z2=z2, y0=y0, top=top, S=S, door=dcell, windows=windows, n=n)
    if roof == "flat" or pk == "Neoterra":
        d.fill(x1, top, z1, x2, top, z2, "smooth_quartz")
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if x in (x1, x2) or z in (z1, z2):
                    d.set(x, top + 1, z, S.get("parapet", "white_concrete"))
                    d.set(x, top + 2, z, "smooth_quartz_slab[type=bottom,waterlogged=false]")
        info["ridge"] = top + 1
        return info
    ridge = d.gable(x1, z1, x2, z2, top, axis, S["roofst"], S["roofsl"], S["end"], overhang=1)
    if pk == "Hearthwood":                                 # king post in each framed gable
        mid_a = (z1 + z2) // 2 if axis == "x" else (x1 + x2) // 2
        for y in range(top, ridge):
            for e in ((x1, x2) if axis == "x" else (z1, z2)):
                cx, cz = (e, mid_a) if axis == "x" else (mid_a, e)
                if d.get(cx, y, cz) == f"minecraft:{S['end']}":
                    d.set(cx, y, cz, f"{S['post']}[axis=y]")
    if chim:
        cx, cz = chim
        for y in range(y0, ridge + 2):
            d.set(cx, y, cz, S["chim"])
        d.set(cx, ridge + 2, cz, f"{S['chimcap']}[type=bottom,waterlogged=false]")
    info["ridge"] = ridge
    return info


def eaves(d, cells):
    """Dress the drip line of a building by hand: each (x, z, kind) puts ONE piece on the ground at y=2.
    kinds: butt (rain barrel), logs (firewood stack), comp (compost bin), pot (decorated pot), bush (azalea in a
    planter), fern, lamp (lantern on a post)."""
    for x, z, kind in cells:
        if kind == "butt":
            d.set(x, 2, z, "barrel[facing=up,open=false]")
        elif kind == "logs":
            log = {"Hearthwood": "oak_log", "Cascadia": "spruce_log", "Neoterra": "birch_log"}[d.pack]
            d.set(x, 2, z, f"{log}[axis=x]")
            d.set(x, 3, z, f"{log}[axis=x]")
        elif kind == "comp":
            d.set(x, 2, z, "composter[level=5]")
        elif kind == "pot":
            d.set(x, 2, z, _pot("south"))
        elif kind == "bush":
            d.set(x, 1, z, "moss_block")
            d.set(x, 2, z, "flowering_azalea")
        elif kind == "fern":
            d.set(x, 1, z, "moss_block")
            d.set(x, 2, z, "large_fern[half=lower]")
            d.set(x, 3, z, "large_fern[half=upper]")
        elif kind == "lamp":
            lamppost(d, x, z, h=2, post={"Hearthwood": "dark_oak_fence", "Cascadia": "spruce_fence",
                                         "Neoterra": "birch_fence"}[d.pack])
        else:
            raise ValueError(kind)


def bench_pair(d, x, z, facing, wood, y=2):
    """Outdoor bench of two stair seats starting at (x, z), backs toward `facing`."""
    dx, dz = (1, 0) if facing in ("north", "south") else (0, 1)
    for i in range(2):
        d.set(x + dx * i, y, z + dz * i, stair(f"{wood}_stairs", facing))


def path(d, x1, z1, x2, z2, block):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for z in range(min(z1, z2), max(z1, z2) + 1):
            d.set(x, 1, z, block)


def hedge(d, x1, z1, x2, z2, leaves="oak_leaves"):
    """A clipped hedge along the line (x1, z1)-(x2, z2) given by hand."""
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            d.set(x, 2, z, f"{leaves}[distance=1,persistent=true,waterlogged=false]")


def flowerrow(d, cells, soil="grass_block[snowy=false]"):
    """A flower border written out cell by cell: [(x, z, flower), ...]."""
    for x, z, f in cells:
        d.set(x, 1, z, soil)
        if f.endswith("_bush") or f in ("peony", "lilac"):
            d.set(x, 2, z, f"{f}[half=lower]")
            d.set(x, 3, z, f"{f}[half=upper]")
        else:
            d.set(x, 2, z, f)


def extend_river(big, x1, x2, oz, sz_small, bank="stone_bricks", weir="mossy_stone_bricks"):
    """River over the whole plot depth (the core only covers part of it), banks on both sides."""
    for x in range(x1, x2 + 1):
        for z in range(big.sz):
            if oz <= z < oz + sz_small and z not in (oz, oz + sz_small - 1):
                continue
            big.set(x, 0, z, SOLIDB)
            big.set(x, 1, z, weir if z in (0, big.sz - 1) else WATER)
    for z in range(1, big.sz - 1):
        if oz < z < oz + sz_small - 1:
            continue
        for x in (x1 - 1, x2 + 1):
            big.set(x, 1, z, bank)


def open_weirs(big, x1, x2, oz, sz_small):
    """After pasting the core, its plot-edge weirs sit in the middle of the longer river: turn them into water."""
    for x in range(x1, x2 + 1):
        for z in (oz, oz + sz_small - 1):
            big.set(x, 1, z, WATER)


def waterwheel(d, x, zc, yc, r=2.5, log="stripped_spruce_log"):
    """Undershot wheel standing in the river in the y-z plane at column x."""
    for z in range(int(zc - r - 1), int(zc + r + 2)):
        for y in range(int(yc - r - 1), int(yc + r + 2)):
            dd = ((z - zc) ** 2 + (y - yc) ** 2) ** 0.5
            if r - 0.6 <= dd <= r + 0.4 and y >= 1:
                d.set(x, y, z, f"{log}[axis=x]")
            elif dd < 0.8 and y >= 1:
                d.set(x, y, z, "dark_oak_log[axis=x]")
            elif (abs(z - zc) < 0.6 or abs(y - yc) < 0.6) and dd < r - 0.5 and y >= 1:
                d.set(x, y, z, "dark_oak_fence")


gb_cascadia, gb_neoterra = core_gb_cascadia, core_gb_neoterra            # replaced further down
rg_hearthwood, rg_cascadia, rg_neoterra = core_rg_hearthwood, core_rg_cascadia, core_rg_neoterra


# ----------------------------------------------------------------------------------------------- bridges
def put(d, S, items):
    """Hand-written absolute placements: (x, y, z, kind, arg)."""
    for x, y, z, kind, arg in items:
        piece(d, kind, x, y, z, arg, S)


def gb_hearthwood(rel, L):
    OX, OZ = 13, 9
    big = Design("Hearthwood", rel, (59, 30, 41), gy=1, paving="grass_block[snowy=false]")
    small = core_gb_hearthwood(rel, L)
    extend_river(big, 9 + OX, 23 + OX, OZ, small.sz)
    paste(big, small, OX, OZ)
    open_weirs(big, 9 + OX, 23 + OX, OZ, small.sz)
    d = big
    road = "gravel" if L < 3 else "cobblestone"
    for x in list(range(0, OX)) + list(range(OX + 33, d.sx)):
        for z in range(19, 22):
            d.set(x, 1, z, road if (x + z) % 5 else ("mossy_cobblestone" if L >= 3 else "coarse_dirt"))
    if L >= 2:
        # ---- Toll House: the toll keeper's office, fire on the west wall, desk facing the door
        b = building(d, 4, 11, 10, 17, 1, door="south", hearth=(5, 14, "east"), pal=0)
        plan(d, b, 0, ["9m77b",
                       "..1..",
                       ".2d.8",
                       ".R@Re",
                       "pR.Rb"])
        put(d, b["S"], [(7, 4, 18, "sign", ("south", ["Toll", "House"])), (6, 4, 18, "torch", "south"),
                        (8, 4, 18, "torch", "south"), (9, 2, 18, "box", ("south", "poppy")),
                        (3, 3, 13, "shutter", "west"), (3, 3, 15, "shutter", "west"),
                        (11, 2, 16, "hay", None), (11, 2, 18, "barrel", None), (11, 3, 18, "pot", "south")])
        bench_pair(d, 1, 17, "north", "dark_oak")
    if L >= 3:
        # ---- The Ferryman: taproom with kegs and bar, stools, settle by the fire; guest room upstairs
        b = building(d, 46, 8, 56, 16, 2, door="south", ladder=(47, 9, "south"), hearth=(55, 12, "west"), pal=1)
        plan(d, b, 0, [".xxP7xxKb",
                       ".........",
                       ".ccdcec..",
                       ".333334..",
                       "......4..",
                       "b4T2.4T2p",
                       "P.l...l.b"], face={"K": "south"})
        plan(d, b, 1, [".vnvjvnv7",
                       ".........",
                       "..R@RR@R.",
                       "........8",
                       "b.......B",
                       "6..4t2...",
                       "p.......p"])
        put(d, b["S"], [(51, 4, 17, "sign", ("south", ["The", "Ferryman"])), (50, 4, 17, "torch", "south"),
                        (52, 4, 17, "torch", "south"), (48, 2, 17, "box", ("south", "poppy")),
                        (54, 2, 17, "box", ("south", "oxeye_daisy")), (48, 7, 17, "box", ("south", "cornflower")),
                        (51, 7, 17, "box", ("south", "poppy")), (54, 7, 17, "box", ("south", "allium")),
                        (48, 2, 18, "barrel", None), (54, 2, 18, "barrel", None), (54, 3, 18, "pot", "south")])
        lamppost(d, 45, 17, post="dark_oak_fence")
        bench_pair(d, 52, 19, "south", "dark_oak")
        hedge(d, 46, 3, 56, 3)
        tree(d, 51, 2, h=4)
        eaves(d, [(45, 7, "butt"), (57, 7, "logs"), (57, 17, "pot")])
    if L >= 4:
        # ---- Bridge Mill: millstone floor with sacks and grain, loft above; the wheel turns in the river
        b = building(d, 13, 32, 20, 39, 2, door="north", ladder=(19, 38, "north"), pal=2)
        plan(d, b, 0, ["s...Bs",
                       "h....b",
                       "s.GV.h",
                       "h....s",
                       "s.....",
                       "hhsB.."], face={"G": "north", "V": "north"})
        plan(d, b, 1, ["sshhss",
                       "......",
                       "s.ll.s",
                       "h....h",
                       "s.....",
                       "hssB.."])
        put(d, b["S"], [(16, 4, 31, "sign", ("north", ["Bridge", "Mill"])), (15, 4, 31, "torch", "north"),
                        (18, 2, 31, "box", ("north", "poppy")), (15, 7, 31, "box", ("north", "allium")),
                        (18, 7, 31, "box", ("north", "poppy")), (14, 2, 31, "sacks", None), (13, 2, 31, "barrel", None)])
        waterwheel(d, 22, 35.5, 3, 2.5)
        # ---- Miller's Cottage: kitchen with range and dining table, settle by the fire; bedroom upstairs
        b = building(d, 2, 25, 10, 33, 2, door="north", ladder=(9, 32, "north"), hearth=(3, 29, "east"), pal=3)
        plan(d, b, 0, ["pc...cb",
                       "b.l...K",
                       "......F",
                       "..2...C",
                       ".11...c",
                       "pTt...B",
                       "b33...."], face={"K": "west", "F": "west"})
        plan(d, b, 1, ["jv.9.vn",
                       ".......",
                       "6.R@R.8",
                       "..RoR..",
                       "b......",
                       "4t2....",
                       "p...B.."])
        put(d, b["S"], [(6, 4, 24, "sign", ("north", ["Miller's", "Cottage"])), (5, 4, 24, "torch", "north"),
                        (4, 2, 24, "box", ("north", "cornflower")), (4, 7, 24, "box", ("north", "poppy")),
                        (7, 7, 24, "box", ("north", "oxeye_daisy"))])
        flowerrow(d, [(2, 35, "poppy"), (3, 35, "oxeye_daisy"), (4, 35, "rose_bush"), (5, 35, "cornflower"),
                      (6, 35, "allium"), (7, 35, "poppy"), (8, 35, "peony"), (9, 35, "oxeye_daisy"),
                      (10, 35, "cornflower")])
        for x in range(1, 12):
            d.set(x, 2, 37, "oak_fence")
        for z in (23, 22):
            d.set(6, 1, z, "gravel")
        path(d, 16, 23, 16, 31, "gravel")
    if L >= 5:
        # ---- Guild Hall: wool market with sales counters below, council chamber with long table above
        b = building(d, 46, 25, 56, 34, 2, door="north", ladder=(55, 33, "north"), hearth=(47, 29, "east"), pal=4)
        plan(d, b, 0, ["bs.....sb",
                       "..l...l..",
                       ".cec.cdc.",
                       ".2.......",
                       ".........",
                       "6.B.l.B.8",
                       "6.......8",
                       "bs9s9sB.."])
        plan(d, b, 1, ["979.m.979",
                       "....l....",
                       "..1111...",
                       ".4TtTt2..",
                       "..3333...",
                       "R...l...8",
                       "6...Q...8",
                       "pB......."], face={"Q": "north"})
        put(d, b["S"], [(51, 4, 24, "sign", ("north", ["Guild", "Hall"])), (50, 4, 24, "torch", "north"),
                        (52, 4, 24, "torch", "north"), (48, 2, 24, "box", ("north", "poppy")),
                        (54, 2, 24, "box", ("north", "poppy")), (48, 7, 24, "box", ("north", "allium")),
                        (51, 7, 24, "box", ("north", "cornflower")), (54, 7, 24, "box", ("north", "allium")),
                        (49, 5, 24, "banner", ("north", "blue")), (53, 5, 24, "banner", ("north", "blue"))])
        # ---- Boat House: oars, nets and caulking barrels, a repair bench
        b = building(d, 38, 32, 44, 39, 2, door="west", ladder=(39, 38, "north"), pal=5)
        plan(d, b, 0, ["Bs.bB",
                       "....s",
                       ".....",
                       "....h",
                       "..l.b",
                       "..k.s"])
        plan(d, b, 1, ["WWsWW",                    # net loft: bales of netting and rope
                       ".....",
                       "s.l.B",
                       "....s",
                       "....b",
                       "..pBW"])
        put(d, b["S"], [(37, 4, 35, "sign", ("west", ["Boat", "House"])), (37, 4, 34, "torch", "west")])
        # ---- Bridge Cottage: kitchen-parlour by the fire, bedroom with two beds upstairs
        b = building(d, 2, 1, 10, 8, 2, door="south", ladder=(3, 2, "south"), hearth=(9, 4, "west"), pal=6)
        plan(d, b, 0, [".cKFCcb",
                       "..l....",
                       ".1..4..",
                       "4T2.4..",
                       ".3....B",
                       "pb.l.Pb"], face={"K": "south", "F": "south"})
        plan(d, b, 1, [".9vnvj7",
                       ".......",
                       "..R@R.8",
                       "..RRR.8",
                       "6......",
                       "p4t2..b"])
        put(d, b["S"], [(6, 4, 9, "sign", ("south", ["Bridge", "Cottage"])), (5, 4, 9, "torch", "south"),
                        (7, 4, 9, "torch", "south"), (4, 2, 9, "box", ("south", "poppy")),
                        (4, 7, 9, "box", ("south", "cornflower")), (7, 7, 9, "box", ("south", "oxeye_daisy"))])
        flowerrow(d, [(47, 36, "rose_bush"), (48, 36, "peony"), (49, 36, "rose_bush"), (50, 36, "peony"),
                      (52, 36, "rose_bush"), (53, 36, "peony"), (54, 36, "rose_bush"), (55, 36, "peony")])
        for x, z in ((25, 3), (30, 37), (33, 5)):
            d.set(x, 2, z, "lily_pad")
        tree(d, 12, 3, h=5, log="dark_oak_log", leaves="dark_oak_leaves")
        lamppost(d, 45, 24, post="dark_oak_fence")
        lamppost(d, 11, 22, post="dark_oak_fence")
    connect_walls(d)
    return d


def gb_cascadia(rel, L):
    OX, OZ = 14, 9
    big = Design("Cascadia", rel, (61, 30, 39), gy=1, paving="grass_block[snowy=false]")
    small = core_gb_cascadia(rel, L)
    extend_river(big, 11 + OX, 21 + OX, OZ, small.sz, bank="cobblestone", weir="mossy_cobblestone")
    paste(big, small, OX, OZ)
    open_weirs(big, 11 + OX, 21 + OX, OZ, small.sz)
    d = big
    for x in list(range(0, OX)) + list(range(OX + 33, d.sx)):
        for z in range(17, 22):
            d.set(x, 1, z, "coarse_dirt" if (x + z) % 4 else "gravel")
    if L >= 2:
        # ---- Ranger Station: map table, log-book lectern, desk by the stove
        b = building(d, 3, 9, 10, 15, 1, door="south", hearth=(9, 12, "west"), pal=0)
        plan(d, b, 0, ["m77.Qb",
                       "......",
                       "6.d2..",
                       "R@R...",
                       "pR.R.b"], face={"Q": "south"})
        put(d, b["S"], [(6, 4, 16, "sign", ("south", ["Ranger", "Station"])), (5, 4, 16, "torch", "south"),
                        (8, 2, 16, "box", ("south", "fern")), (2, 3, 10, "shutter", "west"),
                        (2, 3, 12, "shutter", "west"), (2, 2, 16, "barrel", None), (1, 2, 16, "hay", None)])
        lamppost(d, 11, 16, post="spruce_fence")
        tree(d, 5, 3, h=6, log="spruce_log", leaves="spruce_leaves", r=2)
    if L >= 3:
        # ---- General Store: counters, shelves of goods and a porch; the storekeeper's family lives upstairs
        b = building(d, 48, 7, 58, 15, 2, door="south", ladder=(49, 8, "south"), pal=1)
        plan(d, b, 0, [".b77s77Bb",
                       "..l...l..",
                       ".cce.cdc.",
                       ".........",
                       "6.B.l.s.8",
                       "6.......8",
                       "bs.....Hb"])
        plan(d, b, 1, [".9vjvn.97",
                       ".........",
                       "..R@R....",
                       "..RoR...8",
                       "6.......8",
                       ".........",
                       "b4t2..Bpb"])
        for x in range(47, 60):
            d.set(x, 1, 16, "spruce_planks")
            d.set(x, 6, 16, stair("dark_oak_stairs", "north"))
        for x in (47, 52, 54, 59):
            for y in range(2, 6):
                d.set(x, y, 16, "spruce_log[axis=y]")
        put(d, b["S"], [(53, 4, 16, "sign", ("south", ["General", "Store"])), (49, 2, 16, "barrel", None),
                        (57, 2, 16, "barrels", "south"), (50, 2, 16, "chair", "north"), (56, 2, 16, "chair", "north"),
                        (51, 5, 16, "lamp", None), (55, 5, 16, "lamp", None),
                        (50, 7, 16, "box", ("south", "blue_orchid")), (53, 7, 16, "box", ("south", "dandelion")),
                        (56, 7, 16, "box", ("south", "blue_orchid"))])
    if L >= 4:
        # ---- Sawmill: log carriage running to the saw, sharpening bench; lumber loft above
        b = building(d, 14, 29, 23, 37, 2, door="north", ladder=(22, 36, "north"), pal=2)
        plan(d, b, 0, ["bB...B.b",
                       "........",
                       "XXXXVZZ.",
                       "...l....",
                       "k..G....",
                       "ss....h.",
                       "hhs.B..."], face={"V": "west", "G": "north"})
        plan(d, b, 1, ["ZZZ..ZZZ",
                       "........",
                       "k.w...b.",
                       "...l....",
                       "6..A...b",
                       "B.......",
                       "bss.B..."], face={"A": "north"})
        put(d, b["S"], [(18, 4, 28, "sign", ("north", ["Sawmill"])), (17, 4, 28, "torch", "north")])
        waterwheel(d, 25, 33.5, 3, 2.5)
        for z in range(24, 28):                            # log deck in front of the mill
            for x in (15, 17, 19, 21):
                d.set(x, 2, z, "spruce_log[axis=z]")
            d.set(16, 3, z, "spruce_log[axis=z]")
            d.set(20, 3, z, "spruce_log[axis=z]")
        # ---- Bunk House: mess hall with a long table and the cook's range; bunk room upstairs
        b = building(d, 2, 25, 10, 33, 2, door="north", ladder=(9, 32, "north"), hearth=(3, 29, "east"), pal=3)
        plan(d, b, 0, ["bc...KF",
                       "...l..C",
                       ".......",
                       "..1111c",
                       "..TtTT.",
                       "..3333B",
                       "pb....."], face={"K": "south", "F": "south"})
        plan(d, b, 1, ["jv.9.vj",
                       ".......",
                       ">.....<",
                       "n.R@R.n",
                       ">.RRR.<",
                       ".......",
                       "b4t2..."])
        put(d, b["S"], [(6, 4, 24, "sign", ("north", ["Bunk", "House"])), (5, 4, 24, "torch", "north"),
                        (3, 3, 24, "shutter", "north"), (5, 3, 24, "shutter", "north")])
        for x in range(1, 12):
            d.set(x, 2, 35, "spruce_fence")
    if L >= 5:
        # ---- Timberline Hotel: lobby with desk and fireside chairs, dining, kitchen; two floors of rooms
        b = building(d, 48, 25, 58, 35, 3, door="north", ladder=(57, 34, "north"), hearth=(49, 30, "east"), pal=4)
        plan(d, b, 0, ["9b.....b9",
                       "..l...l..",
                       "...cdc...",
                       "..2.3....",
                       "..t...4T2",
                       "..2......",
                       "......4T2",
                       "K......b.",
                       "CFcxxB..."], face={"K": "east", "F": "north"})
        plan(d, b, 1, ["jvnv..vj.",
                       ".........",
                       "6.R@R...8",
                       "6.RoR....",
                       "....l....",
                       ">.......<",
                       "n.......n",
                       ">......b.",
                       "n4t2....."])
        plan(d, b, 2, ["9.v.v.9.7",
                       ".........",
                       "..R@R....",
                       "6.RRR...8",
                       ".........",
                       "b4t2....B",
                       ".........",
                       "pk.....b.",
                       "bB......."])
        for x in range(47, 60):
            d.set(x, 1, 24, "spruce_planks")
            d.set(x, 6, 24, stair("dark_oak_stairs", "south"))
        for x in (47, 52, 54, 59):
            for y in range(2, 6):
                d.set(x, y, 24, "spruce_log[axis=y]")
        put(d, b["S"], [(53, 4, 24, "sign", ("north", ["Timberline", "Hotel"])), (50, 5, 24, "lamp", None),
                        (56, 5, 24, "lamp", None), (49, 2, 24, "chair", "south"), (50, 2, 24, "chair", "south"),
                        (57, 2, 24, "barrel", None), (50, 7, 24, "box", ("north", "blue_orchid")),
                        (53, 7, 24, "box", ("north", "dandelion")), (56, 7, 24, "box", ("north", "blue_orchid")),
                        (50, 12, 24, "box", ("north", "fern")), (56, 12, 24, "box", ("north", "fern"))])
        # ---- Cabin: one-room log cabin with bed, fireside chair, table and cook stove
        b = building(d, 38, 30, 45, 37, 1, door="west", hearth=(44, 33, "west"), pal=5)
        plan(d, b, 0, ["jv.9b7",
                       "......",
                       "....4.",
                       "4T2.4.",
                       "......",
                       "pKFC.b"], face={"K": "north", "F": "north"})
        put(d, b["S"], [(37, 4, 33, "sign", ("west", ["Cabin"])), (37, 4, 32, "torch", "west")])
        # ---- Smithy: forge fire under the chimney, anvil, quench barrel and tool benches
        b = building(d, 2, 1, 9, 7, 1, door="west", hearth=(8, 4, "west"), pal=0)
        plan(d, b, 0, ["bwkGU.",
                       "......",
                       "...A..",
                       "......",
                       "bC.s.B"], face={"G": "south", "U": "south", "A": "north"})
        put(d, b["S"], [(1, 4, 4, "sign", ("west", ["Smithy"])), (1, 4, 3, "torch", "west")])
        for x, z in ((13, 2), (58, 2), (59, 37), (47, 37)):
            tree(d, x, z, h=7, log="spruce_log", leaves="spruce_leaves", r=2)
        for x, z in ((57, 1), (59, 3), (57, 3), (60, 2)):   # fern understorey of the street-corner fir
            d.set(x, 2, z, "fern")
        for x in (13, 47):
            lamppost(d, x, 23, post="spruce_fence")
        for x, z in ((3, 37), (4, 37), (5, 37)):
            d.set(x, 2, z, "spruce_log[axis=x]")
    connect_walls(d)
    return d


def gb_neoterra(rel, L):
    OX, OZ = 15, 9
    big = Design("Neoterra", rel, (63, 32, 45), gy=1, paving="grass_block[snowy=false]")
    small = core_gb_neoterra(rel, L)
    extend_river(big, 10 + OX, 22 + OX, OZ, small.sz, bank="smooth_stone", weir="smooth_stone")
    paste(big, small, OX, OZ)
    open_weirs(big, 10 + OX, 22 + OX, OZ, small.sz)
    d = big
    for x in list(range(0, OX + 1)) + list(range(OX + 32, d.sx)):
        for z in range(19, 26):
            d.set(x, 1, z, "light_gray_concrete" if z in (19, 25) else "gray_concrete")
        d.set(x, 1, 22, "white_concrete" if x % 3 == 0 else "gray_concrete")
        for z in (18, 26):                                 # sidewalks
            d.set(x, 1, z, "smooth_stone")
    if L >= 2:
        # ---- River Cafe: espresso bar on the back wall, pastry counter, two cafe tables, terrace outside
        b = building(d, 3, 9, 11, 16, 1, door="south", pal=0)
        plan(d, b, 0, ["Kcrecb7",
                       ".......",
                       "cgcd...",
                       ".....l.",
                       "4T2.4T2",
                       "z.l...z"], face={"K": "south"})
        put(d, b["S"], [(7, 4, 17, "sign", ("south", ["RIVER", "CAFE"])),
                        (6, 5, 17, "=", "smooth_quartz_slab[type=top,waterlogged=false]"),
                        (7, 5, 17, "=", "smooth_quartz_slab[type=top,waterlogged=false]"),
                        (8, 5, 17, "=", "smooth_quartz_slab[type=top,waterlogged=false]"),
                        (3, 2, 17, "=", "potted_bamboo"), (11, 2, 17, "=", "potted_bamboo")])
        for x in (3, 7, 11):                               # terrace tables by the river walk
            d.set(x, 1, 6, "smooth_stone")
            d.table(x, 2, 6, "birch", "post")
            d.chair(x - 1, 2, 6, "west", "birch", sit=False)
            d.chair(x + 1, 2, 6, "east", "birch", sit=False)
    if L >= 3:
        # ---- Transit Hub: ticket desk, info lectern, rows of waiting benches, bike repair corner
        b = building(d, 49, 8, 60, 16, 1, door="south", pal=1)
        plan(d, b, 0, ["m.cdc.Q.7b",
                       "..l....l..",
                       ".333..333.",
                       "..........",
                       ".333..333.",
                       "kA.......z",
                       "bB...l...b"], face={"Q": "south", "A": "east"})
        put(d, b["S"], [(54, 4, 17, "sign", ("south", ["TRANSIT", "HUB"]))])
        for x in (49, 51, 53, 55, 57, 59):                 # bike stands
            d.set(x, 2, 6, "iron_bars")
            d.set(x, 2, 5, "smooth_stone_slab[type=bottom,waterlogged=false]")
        for x, z in ((48, 3), (61, 3), (48, 17), (61, 17)):
            d.set(x, 2, z, "smooth_quartz")
            d.set(x, 3, z, "sea_lantern")
    if L >= 4:
        # ---- River Lab: monitoring office with desks below, wet lab with island benches above
        b = building(d, 2, 29, 12, 38, 2, door="north", ladder=(11, 37, "north"), pal=2)
        plan(d, b, 0, ["97.....79",
                       "..l...l..",
                       "6.......8",
                       "..d...d..",
                       "..3...3..",
                       "6.......8",
                       "z.t......",
                       "bkQ...B.."], face={"Q": "north"})
        plan(d, b, 1, ["rCr..crc7",
                       ".........",
                       "6.rc.rc.8",
                       "....l....",
                       "6.rc.rc..",
                       ".........",
                       "kQ.......",
                       "bBz...C.."], face={"Q": "north"})
        put(d, b["S"], [(7, 4, 28, "sign", ("north", ["RIVER", "LAB"]))])
        # ---- Kayak Hire: kayaks racked along the walls, hire counter by the door
        b = building(d, 40, 35, 47, 42, 1, door="west", pal=3)
        plan(d, b, 0, ["OOO.YY",
                       "cg....",
                       ".....b",
                       "....l.",
                       "k....s",
                       "YYY.OO"])
        put(d, b["S"], [(39, 4, 38, "sign", ("west", ["KAYAK", "HIRE"]))])
        for x in range(2, 13):
            d.set(x, 1, 27, "smooth_stone")
        for z in (31, 34, 37, 40, 43):
            d.set(39, 1, z, "smooth_stone")
        # riverside seating steps on the west bank, facing the water and the bridge
        for k, x in enumerate((21, 20, 19)):
            for z in range(38, 44):
                for y in range(2, 2 + k):
                    d.set(x, y, z, "smooth_stone")
                d.set(x, 2 + k, z, stair("smooth_quartz_stairs", "west"))
        for z in (37, 44):
            for x in (19, 20, 21):
                d.set(x, 1, z, "smooth_stone")
            d.set(19, 2, z, "moss_block")
            d.set(19, 3, z, "flowering_azalea")
            d.set(21, 2, z, "smooth_quartz")
            d.set(21, 3, z, "sea_lantern")
    if L >= 5:
        # ---- Skyline Residences: lobby, three different apartments, a co-working floor on top
        b = building(d, 50, 29, 60, 39, 5, door="north", ladder=(59, 38, "north"), pal=4)
        plan(d, b, 0, ["z7.....7z",
                       "..l...l..",
                       ".........",
                       "...cdc...",
                       "....3....",
                       "4T2...4T2",
                       "b........",
                       "B........",
                       "pBz...b.."])
        plan(d, b, 1, ["KFCcc...9",
                       "........j",
                       ".11.....<",
                       ".TT.R@R.j",
                       ".33.RoR.<",
                       "....RRR.j",
                       "4t......8",
                       "4.......8",
                       "zJ....b.."], face={"K": "south", "F": "south"})
        plan(d, b, 2, ["97Q...vjv",
                       ".........",
                       "..d...R@R",
                       "..3...RoR",
                       ".........",
                       "6.4t2...8",
                       "6.......8",
                       ".........",
                       "bKCcc.B.."], face={"Q": "south", "K": "north"})
        plan(d, b, 3, ["jvjv.jvj7",
                       ".........",
                       "..R@R....",
                       "..RoR...8",
                       "9.......8",
                       ".........",
                       "4T2..4T2.",
                       ".........",
                       "pKFC..b.."], face={"K": "north", "F": "north"})
        plan(d, b, 4, ["979.m.979",
                       "....l....",
                       "..d..d...",
                       "..3..3...",
                       ".........",
                       "..d..d...",
                       "..3..3...",
                       "6...l....",
                       "kQz...B.."], face={"Q": "north"})
        put(d, b["S"], [(55, 4, 28, "sign", ("north", ["SKYLINE", "RESIDENCES"]))])
        for x, z in ((14, 3), (48, 42), (13, 41)):          # shade trees by the cafe, the kayak hire, the steps
            tree(d, x, z, h=5, log="birch_log", leaves="birch_leaves", r=2)
        for x, z in ((14, 17), (14, 27), (48, 17), (48, 27)):
            d.set(x, 2, z, "smooth_quartz")
            d.set(x, 3, z, "sea_lantern")
        flowerrow(d, [(50, 41, "azure_bluet"), (51, 41, "white_tulip"), (52, 41, "allium"), (53, 41, "azure_bluet"),
                      (55, 41, "lily_of_the_valley"), (56, 41, "allium"), (57, 41, "white_tulip"),
                      (58, 41, "azure_bluet"), (59, 41, "allium")], "moss_block")
    connect_walls(d)
    return d


# ----------------------------------------------------------------------------------------------- granaries
def rg_hearthwood(rel, L):
    OX = 14
    big = Design("Hearthwood", rel, (61, 26, 49), gy=1, paving="grass_block[snowy=false]")
    small = core_rg_hearthwood(rel, L)
    paste(big, small, OX, 0)
    d = big
    for x in range(0, d.sx):                              # farm lane along the street
        for z in (0, 1):
            if d.get(x, 1, z).endswith("grass_block[snowy=false]"):
                d.set(x, 1, z, "dirt_path")
    if L >= 2:
        # ---- Cart Shed: the estate cart under cover, tool bench and grindstone, hay and sacks
        b = building(d, 2, 4, 11, 11, 1, door="south", pal=3)
        plan(d, b, 0, ["bkG...Bb",
                       "........",
                       "........",
                       "h......s",
                       "hh....Ws",
                       "hp...lWs"], face={"G": "south"})
        put(d, b["S"], [(5, 2, 6, "=", "oak_slab[type=top,waterlogged=false]"),
                        (6, 2, 6, "=", "oak_slab[type=top,waterlogged=false]"),
                        (7, 2, 6, "=", "oak_slab[type=top,waterlogged=false]"),
                        (5, 2, 7, "=", "oak_slab[type=top,waterlogged=false]"),
                        (6, 2, 7, "=", "oak_slab[type=top,waterlogged=false]"),
                        (7, 2, 7, "=", "oak_slab[type=top,waterlogged=false]"),
                        (8, 2, 6, "=", "oak_fence"), (8, 2, 7, "=", "oak_fence"),
                        (6, 3, 6, "hay", None), (5, 3, 7, "sacks", None),
                        (6, 4, 12, "sign", ("south", ["Cart", "Shed"])), (5, 4, 12, "torch", "south")])
        for x in (4, 9):                                   # the hay wain waiting outside
            d.set(x, 2, 14, "oak_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
        for x in (5, 6, 7, 8):
            d.set(x, 2, 14, "hay_block[axis=x]")
        d.set(6, 3, 14, "hay_block[axis=x]")
        d.set(10, 2, 14, "oak_fence")
    if L >= 3:
        # ---- Royal Stables: three stalls with mangers and water, tack corner; hay loft above
        b = building(d, 49, 4, 59, 12, 2, door="south", ladder=(58, 11, "north"), pal=4)
        plan(d, b, 0, ["HCEHCEHCh",
                       "..E..E...",
                       "..E..E...",
                       ".........",
                       "s...l...b",
                       "M........",
                       "bB......."], face={"M": "east"})
        plan(d, b, 1, ["hhhhhhhhh",
                       "HH.HH.HHs",
                       ".........",
                       "s...l...s",
                       "hh.....hh",
                       "H.......H",
                       "sW......."])
        put(d, b["S"], [(54, 4, 13, "sign", ("south", ["Royal", "Stables"])), (53, 4, 13, "torch", "south"),
                        (55, 4, 13, "torch", "south"), (52, 2, 14, "cauldron", None), (56, 2, 14, "hay", None)])
        eaves(d, [(48, 3, "butt"), (60, 3, "comp"), (48, 13, "logs"), (60, 13, "butt")])
        for x in range(48, 61):                            # paddock rail with two gates
            gate = x in (50, 58)
            d.set(x, 2, 15, "oak_fence_gate[facing=south,in_wall=false,open=false,powered=false]" if gate else "oak_fence")
        # ---- Dutch hay barrack by the stable yard: four posts, a stack of hay and a sliding roof over it
        for x, z in ((55, 23), (59, 23), (55, 26), (59, 26)):
            for y in range(2, 7):
                d.set(x, y, z, "stripped_dark_oak_log[axis=y]")
        for x in range(56, 59):
            for z in range(23, 27):
                for y in range(2, 5 if z in (23, 26) else 6):
                    d.set(x, y, z, "hay_block[axis=y]")
        for x in range(55, 60):
            for z in range(23, 27):
                d.set(x, 7, z, slab("dark_oak_slab", "bottom"))
        # ---- Seed Granary: sacks and seed bins, the weighing counter by the door
        b = building(d, 2, 17, 10, 24, 1, door="east", pal=5)
        plan(d, b, 0, ["sWsWsBb",
                       ".......",
                       "h.cdc..",
                       "h......",
                       "H.....l",
                       "hhsWsB."])
        put(d, b["S"], [(11, 4, 20, "sign", ("east", ["Seed", "Granary"])), (11, 4, 19, "torch", "east")])
    if L >= 4:
        # ---- Steward's House: estate office with map table and ledger lectern, fireside chairs, dining table and
        #      range; bedroom and study upstairs
        b = building(d, 2, 28, 12, 37, 2, door="north", ladder=(11, 36, "north"), hearth=(3, 32, "east"), pal=6)
        plan(d, b, 0, ["9m9...Q.7",
                       "..l......",
                       "..2......",
                       "..t......",
                       "..2......",
                       "....1111.",
                       "b...TtTT.",
                       "pKF.3333."], face={"Q": "south", "K": "north", "F": "north"})
        plan(d, b, 1, ["jv.....vj",
                       ".........",
                       "6.R@R...8",
                       "6.RoR....",
                       "..RRR....",
                       "b......2t",
                       ".........",
                       "9.Q...B.."], face={"Q": "north"})
        put(d, b["S"], [(7, 4, 27, "sign", ("north", ["Steward's", "House"])), (6, 4, 27, "torch", "north"),
                        (8, 4, 27, "torch", "north"), (4, 2, 27, "box", ("north", "poppy")),
                        (10, 2, 27, "box", ("north", "cornflower")), (4, 7, 27, "box", ("north", "allium")),
                        (7, 7, 27, "box", ("north", "poppy")), (10, 7, 27, "box", ("north", "oxeye_daisy"))])
        eaves(d, [(1, 27, "pot"), (13, 27, "butt"), (1, 38, "logs"), (13, 38, "comp")])
        flowerrow(d, [(2, 25, "poppy"), (3, 25, "rose_bush"), (4, 25, "cornflower"), (5, 25, "oxeye_daisy"),
                      (9, 25, "allium"), (10, 25, "peony"), (11, 25, "poppy"), (12, 25, "cornflower")])
        # ---- Malt House: barley spread on the malting floor, kiln furnaces; grain loft above
        b = building(d, 48, 28, 58, 37, 2, door="north", ladder=(57, 36, "north"), pal=7)
        plan(d, b, 0, ["Bs.....sB",
                       ".........",
                       ".HHH.HHH.",
                       ".HHH.HHH.",
                       "....l....",
                       "U........",
                       "F...C...b",
                       "bss.B...."], face={"U": "east", "F": "east"})
        plan(d, b, 1, ["shshshshs",
                       ".........",
                       "s.B...B.s",
                       "h.......h",
                       "s...l...s",
                       "h.......h",
                       ".........",
                       "sWs.Bs..."])
        put(d, b["S"], [(53, 4, 27, "sign", ("north", ["Malt", "House"])), (52, 4, 27, "torch", "north")])
        r = b["ridge"]                                     # louvred kiln cowl on the ridge
        for x in (52, 54):
            for z in (31, 33):
                for y in range(r, r + 3):
                    d.set(x, y, z, "stripped_dark_oak_log[axis=y]")
        for x, z, f in ((53, 31, "north"), (53, 33, "south"), (52, 32, "west"), (54, 32, "east")):
            for y in (r + 1, r + 2):
                d.set(x, y, z, f"spruce_trapdoor[facing={f},half=bottom,open=true,powered=false,waterlogged=false]")
        for x in range(51, 56):
            for z in range(30, 35):
                d.set(x, r + 3, z, stair("mud_brick_stairs", "south" if z > 32 else "north") if z != 32 else slab("mud_brick_slab", "bottom"))
        d.set(53, r + 4, 32, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        for z in range(23, 28):
            d.set(7, 1, z, "gravel")
            d.set(53, 1, z, "gravel")
        lamppost(d, 13, 27)
        lamppost(d, 47, 27)
        bench_pair(d, 9, 26, "south", "dark_oak")          # bench under the steward's windows
        # ---- orchard behind the steward's house: two rows of apple trees, hives between them, a hurdle fence
        for x in range(1, 13):
            for z in (40, 47):
                d.set(x, 2, z, "oak_fence")
        for z in range(41, 47):
            d.set(1, 2, z, "oak_fence")
            d.set(12, 2, z, "oak_fence")
        d.set(7, 2, 40, "oak_fence_gate[facing=north,in_wall=false,open=false,powered=false]")
        for x, z in ((3, 42), (7, 42), (10, 42), (3, 45), (7, 45), (10, 45)):
            tree(d, x, z, h=4, leaves="oak_leaves", r=1)
        for x in (5, 9):
            d.set(x, 2, 44, "beehive[facing=south,honey_level=3]")
        for z in range(41, 47):
            d.set(7, 1, z, "dirt_path") if z not in (42, 45) else None
        d.set(5, 2, 41, "composter[level=7]")
        bench_pair(d, 8, 46, "south", "oak")
        # ---- walled kitchen garden behind the barn
        for x in range(14, 47):
            for z in (41, 47):
                d.set(x, 2, z, "cobblestone_wall")
        for z in range(41, 48):
            d.set(14, 2, z, "cobblestone_wall")
            d.set(46, 2, z, "cobblestone_wall")
        d.set(30, 2, 41, AIR)
        crops = (("wheat[age=7]", 17, 19), ("carrots[age=7]", 21, 23), ("potatoes[age=7]", 25, 27),
                 ("beetroots[age=3]", 29, 31), ("wheat[age=7]", 33, 35), ("carrots[age=7]", 37, 39),
                 ("potatoes[age=7]", 41, 43))
        for x in range(16, 45):                            # gravel walk between the beds
            d.set(x, 1, 42, "gravel")
            d.set(x, 1, 46, "gravel")
        for crop, xa, xb in crops:
            for x in range(xa, xb + 1):
                for z in (43, 44, 45):
                    d.set(x, 1, z, "farmland[moisture=7]")
                    d.set(x, 2, z, crop)
        for x in (16, 44):
            tree(d, x, 39, h=4, leaves="oak_leaves", r=1)
        for x, z in ((14, 41), (46, 41), (14, 47), (46, 47)):  # gate piers with lamps
            d.set(x, 3, z, "cobblestone_wall")
            d.set(x, 4, z, lantern())
        for x in range(48, 59):                            # malt-house yard fence with a gate
            d.set(x, 2, 26, "oak_fence_gate[facing=north,in_wall=false,open=false,powered=false]" if x == 53 else "oak_fence")
    if L >= 5:
        # ---- Bake House: ovens on the back wall, kneading table, bread counters by the door; flour loft and
        #      the baker's bed above
        b = building(d, 17, 30, 27, 38, 2, door="north", ladder=(18, 37, "north"), hearth=(26, 34, "west"), pal=8)
        plan(d, b, 0, ["gce...ecg",
                       "....l....",
                       "s..ccc...",
                       "s........",
                       "W..ccc...",
                       "........ ",
                       ".KFFKCbb."], face={"K": "north", "F": "north"})
        plan(d, b, 1, ["jv.9..sWs",
                       "........s",
                       "..R@R...s",
                       "..RoR...W",
                       "6........",
                       "b4t2....s",
                       "..B...sWs"])
        put(d, b["S"], [(22, 4, 29, "sign", ("north", ["Bake", "House"])), (21, 4, 29, "torch", "north")])
        # ---- Tithe Office: tithe counter with the clerks behind it, ledgers and strongbox barrels; clerk's
        #      home upstairs
        b = building(d, 33, 30, 43, 38, 2, door="north", ladder=(42, 37, "north"), hearth=(34, 34, "east"), pal=9)
        plan(d, b, 0, ["z.......z",
                       "..l...l..",
                       ".cdc.cec.",
                       "..2.3..3.",
                       ".........",
                       "6.......8",
                       "9B9QBb9.."], face={"Q": "north"})
        plan(d, b, 1, ["9jv.vj..7",
                       ".........",
                       "..R@R....",
                       "..RoR...8",
                       "6........",
                       "6.4t2....",
                       "pb....B.."])
        put(d, b["S"], [(38, 4, 29, "sign", ("north", ["Tithe", "Office"])), (37, 4, 29, "torch", "north"),
                        (39, 4, 29, "torch", "north")])
        # ---- Alms House: shared kitchen and table, two dormitory rooms, a prayer room at the top
        b = building(d, 49, 40, 58, 47, 3, door="west", ladder=(57, 46, "north"), hearth=(57, 43, "west"), pal=10)
        plan(d, b, 0, ["KFCcc.bp",
                       "...l....",
                       "..1111..",
                       "..TtTT..",
                       "..3333..",
                       "pb....B."], face={"K": "south", "F": "south"})
        plan(d, b, 1, ["jv.vj.vj",
                       "........",
                       ".R@R....",
                       "........",
                       "........",
                       "^j^..b.."])
        plan(d, b, 2, ["p......9",
                       ".4.4....",
                       ".4.4..Q.",
                       ".4.4.l..",
                       ".4.4....",
                       "p......."], face={"Q": "west"})
        put(d, b["S"], [(48, 4, 43, "sign", ("west", ["Alms", "House"])), (48, 4, 42, "torch", "west")])
        # ---- Brew House: mash tuns and the brewing bench on the ground floor, kegs along the north wall;
        #      hop and malt loft with the brewer's bed upstairs
        b = building(d, 47, 16, 59, 22, 3, door="south", doorpos=53, ladder=(48, 17, "south"),
                     hearth=(58, 19, "west"), pal=2)
        plan(d, b, 0, [".CrC..xxxxb",
                       "....l......",
                       "s.cdc......",
                       "s......2l..",
                       "WsB.....ybp"])
        plan(d, b, 1, [".hhsWs.ssWs",
                       "...........",
                       "h...l......",
                       "s..R@R...vj",
                       "Ws.4t2....."])
        plan(d, b, 2, [".7..vj.jv.9",               # the brewer's family flat in the roof storey
                       "...........",
                       "6..R@R....8",
                       "...........",
                       "pKFC.4T2..b"], face={"K": "north", "F": "north"})
        put(d, b["S"], [(55, 4, 23, "sign", ("south", ["Brew", "House"])), (54, 4, 23, "torch", "south"),
                        (51, 2, 23, "barrel", None), (50, 2, 23, "keg", "east"), (56, 2, 23, "box", ("south", "poppy"))])

    connect_walls(d)
    return d


def rg_cascadia(rel, L):
    OX = 13
    big = Design("Cascadia", rel, (57, 34, 51), gy=1, paving="coarse_dirt")
    small = core_rg_cascadia(rel, L)
    paste(big, small, OX, 0)
    d = big
    for x in list(range(0, OX)) + list(range(OX + 31, d.sx)):
        for z in (1, 2, 3):
            d.set(x, 1, z, "gravel")
        d.set(x, 2, 2, "rail[shape=east_west,waterlogged=false]")
        if x % 2 == 0:
            d.set(x, 1, 2, "spruce_planks")
    if L >= 2:
        # ---- Scale House: the weighmaster's ledger lectern, desk by the stove, sacks waiting to be weighed
        b = building(d, 2, 6, 10, 12, 1, door="north", hearth=(9, 9, "west"), pal=3)
        plan(d, b, 0, ["9Q...b.",
                       ".......",
                       "..d2...",
                       "R@R....",
                       "pRR.s.b"], face={"Q": "south"})
        put(d, b["S"], [(6, 4, 5, "sign", ("north", ["Scale", "House"])), (5, 4, 5, "torch", "north")])
        for x in range(3, 10):                             # the wagon scale plate in front
            d.set(x, 1, 4, "smooth_stone")
        # hay yard behind the scale house: split-rail pen, three ricks, a farm wagon and the woodpile
        for x in range(1, 12):
            d.set(x, 2, 17, "spruce_fence")
        for z in (14, 15, 16):
            d.set(1, 2, z, "spruce_fence")
            d.set(11, 2, z, "spruce_fence")
        for x0 in (2, 5):
            for x in (x0, x0 + 1):
                for z in (15, 16):
                    d.set(x, 2, z, "hay_block[axis=y]")
                    d.set(x, 3, z, "hay_block[axis=x]")
        d.set(8, 2, 16, "hay_block[axis=y]")
        for x in (7, 10):
            d.set(x, 2, 14, "spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
        for x in (8, 9):
            d.set(x, 2, 14, "spruce_slab[type=top,waterlogged=false]")
            d.set(x, 3, 14, "hay_block[axis=x]")
        for z in (15, 16):
            for y in (2, 3):
                d.set(10, y, z, "spruce_log[axis=x]")
        d.set(9, 2, 16, "barrel[facing=up,open=false]")
        for x, z in ((3, 14), (4, 14), (5, 14)):            # a rick being built: hay on a log bed
            d.set(x, 2, z, "spruce_log[axis=x]")
            d.set(x, 3, z, "hay_block[axis=x]")
        d.set(4, 4, 14, "hay_block[axis=x]")
        lamppost(d, 12, 13, post="spruce_fence")
        for x in (1, 11):                                  # lamps at the ends of the wagon scale
            lamppost(d, x, 4, post="spruce_fence")
    if L >= 3:
        # ---- Feed & Seed: rack bays of barrels and sacks on two floors, loading dock on the siding
        b = building(d, 45, 6, 55, 14, 2, door="north", ladder=(54, 13, "north"), pal=4)
        plan(d, b, 0, ["Bs.....sB",
                       "....l....",
                       "B.B...B.B",
                       "s.s...s.s",
                       "B.B...B.B",
                       "....l....",
                       "hhsWs.B.."])
        plan(d, b, 1, ["WsWsWsWsW",
                       ".........",
                       "h.h...h.h",
                       "h.s...s.h",
                       "s.h...h.s",
                       "....l....",
                       "hshs.Bs.."])
        for x in range(45, 56):
            d.set(x, 1, 5, "spruce_planks")
            d.set(x, 1, 4, "spruce_planks")
        put(d, b["S"], [(50, 4, 5, "sign", ("north", ["Feed &", "Seed"])), (46, 2, 4, "barrel", None),
                        (48, 2, 4, "barrel", None), (53, 2, 4, "barrel", None), (54, 2, 4, "sacks", "white_wool")])
        eaves(d, [(44, 5, "butt"), (56, 5, "logs"), (44, 15, "logs"), (56, 15, "butt")])
        # ---- water tower: a stave tank on a log trestle, the spout swung toward the yard
        for x in (48, 52):
            for z in (44, 48):
                for y in range(2, 6):
                    d.set(x, y, z, "spruce_log[axis=y]")
        for x in range(48, 53):
            d.set(x, 4, 46, "stripped_spruce_log[axis=x]")
        for x in range(47, 54):
            for z in range(43, 50):
                d.set(x, 6, z, "spruce_planks" if 48 <= x <= 52 and 44 <= z <= 48 else slab("spruce_slab", "top"))
        for x in range(48, 53):
            for z in range(44, 49):
                ring_ = x in (48, 52) or z in (44, 48)
                corner = x in (48, 52) and z in (44, 48)
                for y in range(7, 11):
                    if corner:
                        d.set(x, y, z, "spruce_log[axis=y]")
                    elif ring_:
                        d.set(x, y, z, "stripped_spruce_log[axis=y]" if y != 9 else "dark_oak_planks")
                    else:
                        d.set(x, y, z, WATER)
                d.set(x, 11, z, slab("dark_oak_slab", "bottom") if ring_ else "dark_oak_planks")
        d.set(50, 12, 46, "dark_oak_slab[type=bottom,waterlogged=false]")
        for y in range(7, 10):
            d.set(53, y, 46, "chain[axis=y,waterlogged=false]")
        d.set(53, 10, 46, "spruce_fence")
        for y in range(2, 7):
            d.set(48, y, 49, "ladder[facing=south,waterlogged=false]")
    if L >= 4:
        # ---- Feed Mill: millstones and mixing tub on the ground floor, repair shop above
        b = building(d, 2, 33, 12, 42, 2, door="north", ladder=(11, 41, "north"), pal=5)
        plan(d, b, 0, ["sB.....Bs",
                       ".........",
                       "s.GVG...s",
                       "h.......h",
                       "s...l...s",
                       "k..C.....",
                       ".........",
                       "hss.WsB.."], face={"G": "north", "V": "north"})
        plan(d, b, 1, ["kwG...Bbb",
                       ".........",
                       "6..A....8",
                       ".........",
                       "6...l...8",
                       ".........",
                       "XX.......",
                       "bsk...B.."], face={"G": "south", "A": "north"})
        put(d, b["S"], [(7, 4, 32, "sign", ("north", ["Feed", "Mill"])), (6, 4, 32, "torch", "north")])
        # ---- Bunk House: kitchen, card table and fireside chair below, rows of bunks above
        b = building(d, 44, 33, 54, 42, 2, door="north", ladder=(53, 41, "north"), hearth=(45, 37, "east"), pal=6)
        plan(d, b, 0, ["KFCc...bp",
                       ".........",
                       ".......xx",
                       "..2..1...",
                       "....4T2..",
                       ".....3...",
                       "6........",
                       "b.B.s.B.."], face={"K": "south", "F": "south"})
        plan(d, b, 1, ["vjvjvjvjv",
                       ".........",
                       "...R@R...",
                       ".........",
                       ".........",
                       "^j^j^j^..",
                       ".........",
                       "b4t2..B.."])
        put(d, b["S"], [(49, 4, 32, "sign", ("north", ["Bunk", "House"])), (48, 4, 32, "torch", "north")])
        for x, z in ((1, 30), (55, 30), (28, 48)):
            tree(d, x, z, h=6, log="spruce_log", leaves="spruce_leaves", r=2)
    if L >= 5:
        # ---- Grain Co-op Hall: co-op store, board room with the long table, manager's flat at the top
        b = building(d, 18, 36, 30, 46, 3, door="north", ladder=(29, 45, "north"), hearth=(19, 41, "east"), pal=7)
        plan(d, b, 0, ["bB.......Bb",
                       "...l...l...",
                       ".cec...cdc.",
                       "...........",
                       "..2........",
                       "...B.B.B.B.",
                       "6.........8",
                       "6...l.....8",
                       "sWsBsWs.h.."])
        plan(d, b, 1, ["979..m..979",
                       "...........",
                       "..d..d..d..",
                       "..3..3..3..",
                       "...........",
                       "..1111111..",
                       ".4TTtTtTT2.",
                       "..3333333..",
                       "pQ.....B..."], face={"Q": "north"})
        plan(d, b, 2, ["jv.9..vjv.7",
                       "...........",
                       "...R@R....8",
                       "...RoR....8",
                       "6..........",
                       "6.4t2......",
                       "...........",
                       "KFCc..4T2..",
                       "b.....B...."], face={"K": "north", "F": "north"})
        put(d, b["S"], [(24, 4, 35, "sign", ("north", ["Grain", "Co-op Hall"])), (23, 4, 35, "torch", "north"),
                        (25, 4, 35, "torch", "north")])
        # ---- Grain Shed: bulk sacks and bales on two floors
        b = building(d, 35, 38, 42, 46, 2, door="west", ladder=(41, 39, "south"), pal=8)
        plan(d, b, 0, ["hhsW..",
                       "......",
                       "s.h..h",
                       "...l.s",
                       "s.h..h",
                       "......",
                       "hsWshh"])
        plan(d, b, 1, ["sWs...",
                       "......",
                       "h.s..s",
                       "h..l.h",
                       "s.h..s",
                       "......",
                       "BhsWsB"])
        put(d, b["S"], [(34, 4, 42, "sign", ("west", ["Grain", "Shed"]))])
        # ---- Tool Shed: workbench, grindstone, anvil, timber
        b = building(d, 4, 45, 12, 50, 1, door="east", pal=9)
        plan(d, b, 0, ["kGwAbBb",
                       ".......",
                       "h..l...",
                       "hsXXX.b"], face={"G": "south", "A": "south"})
        put(d, b["S"], [(13, 4, 47, "sign", ("east", ["Tool", "Shed"]))])
        # ---- Post & Telegraph: post counter and sorting shelves below, the operator's desk and family above
        b = building(d, 1, 19, 11, 28, 2, door="east", doorpos=23, ladder=(2, 20, "south"),
                     hearth=(2, 25, "east"), pal=2)
        plan(d, b, 0, [".9779.Q.b",
                       "...l.....",
                       "..cdcec..",
                       "...3.3...",
                       ".........",
                       "...4T2...",
                       "..l......",
                       "pb.B..4.b"], face={"Q": "south"})
        plan(d, b, 1, [".m.d..vjv",
                       "...3.....",
                       "6.......8",
                       "..R@R....",
                       "..RoR...8",
                       "......l..",
                       "4t2......",
                       "KFC....Bp"], face={"K": "north", "F": "north"})
        put(d, b["S"], [(12, 4, 24, "sign", ("east", ["Post &", "Telegraph"])), (12, 4, 22, "torch", "east"),
                        (12, 2, 21, "barrel", None), (12, 2, 26, "chair", "east"), (12, 2, 27, "chair", "east")])
        for y in range(2, 13):                             # telegraph pole by the door
            d.set(13, y, 19, "spruce_fence" if y < 12 else "spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
        for x in (16, 32):
            lamppost(d, x, 34, post="spruce_fence")
        for x, z in ((14, 48), (43, 48), (55, 48)):
            tree(d, x, z, h=7, log="spruce_log", leaves="spruce_leaves", r=2)
        for x, z in ((54, 47), (56, 49), (54, 49), (56, 47), (55, 50)):   # ferns under the back fir
            d.set(x, 2, z, "fern")
    connect_walls(d)
    return d


def rg_neoterra(rel, L):
    OX = 14
    big = Design("Neoterra", rel, (61, 32, 55), gy=1, paving="grass_block[snowy=false]")
    small = core_rg_neoterra(rel, L)
    paste(big, small, OX, 0)
    d = big
    for x in list(range(0, OX)) + list(range(OX + 33, d.sx)):
        for z in range(0, 5):
            d.set(x, 1, z, "smooth_stone" if (x + z) % 4 else "light_gray_concrete")
    if L >= 2:
        # ---- Security Gate: guard desk and lockers below, monitor wall and briefing table above
        b = building(d, 2, 7, 11, 14, 2, door="north", ladder=(10, 13, "north"), pal=3)
        plan(d, b, 0, ["9Q....cd",
                       "...l....",
                       "..d2....",
                       "........",
                       "6......B",
                       "bbB.r..."], face={"Q": "south"})
        plan(d, b, 1, ["m.Q.Q..9",
                       "..3.3...",
                       "........",
                       "4TT2....",
                       "........",
                       "z..l..B."], face={"Q": "south"})
        put(d, b["S"], [(6, 4, 6, "sign", ("north", ["SECURITY", "GATE"]))])
        for x in (1, 4, 7, 10):
            d.set(x, 2, 5, "smooth_quartz")
            d.set(x, 3, 5, "sea_lantern")
        for x, z in ((1, 16), (4, 16), (9, 16), (12, 16)):     # planter boxes along the gate's back walk
            d.set(x, 1, z, "moss_block")
            d.set(x, 2, z, "flowering_azalea" if x in (1, 12) else "azalea")
        for x in (2, 10):
            d.set(x, 2, 16, "smooth_quartz_slab[type=bottom,waterlogged=false]")
            d.set(x + 1, 2, 16, "smooth_quartz_slab[type=bottom,waterlogged=false]")
        for x in range(1, 13):
            d.set(x, 1, 15, "smooth_stone")
        # covered bike shelter for the guards, behind the planters
        for x in (2, 8):
            for z in (18, 20):
                for y in (2, 3, 4):
                    d.set(x, y, z, "light_gray_concrete")
        for x in range(2, 9):
            for z in range(18, 21):
                d.set(x, 5, z, "smooth_quartz_slab[type=bottom,waterlogged=false]")
                d.set(x, 1, z, "smooth_stone")
        for x in (3, 5, 7):
            d.set(x, 2, 19, "iron_bars")
        d.set(5, 4, 19, lantern(True))
    if L >= 3:
        # ---- Gene Lab: wet lab with island benches, data office upstairs
        b = building(d, 48, 5, 58, 13, 2, door="north", ladder=(57, 12, "north"), pal=4)
        plan(d, b, 0, ["rCr.....7",
                       ".........",
                       "6.rc.rc.8",
                       "....l....",
                       "6.rc.cr.8",
                       ".........",
                       "kQ..B.b.."], face={"Q": "north"})
        plan(d, b, 1, ["979.m.979",
                       ".........",
                       ".d..d..d.",
                       ".3..3..3.",
                       ".........",
                       "4t2......",
                       "z...l.B.."])
        put(d, b["S"], [(53, 4, 4, "sign", ("north", ["GENE", "LAB"]))])
        flowerrow(d, [(48, 15, "azure_bluet"), (49, 15, "white_tulip"), (50, 15, "allium"), (52, 15, "azure_bluet"),
                      (54, 15, "white_tulip"), (56, 15, "allium"), (57, 15, "azure_bluet"), (58, 15, "white_tulip")],
                  "moss_block")
    if L >= 4:
        # ---- Crop Research: seed-tray benches below, seed analysis lab above
        b = building(d, 2, 34, 12, 44, 2, door="north", ladder=(11, 43, "north"), pal=5)
        plan(d, b, 0, ["rcg...gcr",
                       ".........",
                       "6.iii.gg.",
                       ".........",
                       "6.ggg.ii.",
                       "....l....",
                       "C.iii.gg.",
                       ".........",
                       "kQ.B..b.."], face={"Q": "north"})
        plan(d, b, 1, ["rCr..rcr7",
                       ".........",
                       "6.rc.cr.8",
                       ".........",
                       "6.cr.rc.8",
                       "....l....",
                       ".d..d..d.",
                       ".3..3..3.",
                       "bB....b.."])
        put(d, b["S"], [(7, 4, 33, "sign", ("north", ["CROP", "RESEARCH"]))])
        # ---- Logistics: rack aisles below, dispatch office above
        b = building(d, 48, 34, 58, 44, 2, door="north", ladder=(57, 43, "north"), pal=6)
        plan(d, b, 0, ["Bb.....bB",
                       ".........",
                       "B.B...B.B",
                       "B.B...B.B",
                       "s.s...s.s",
                       "B.B.l.B.B",
                       "B.B...B.B",
                       ".........",
                       "hsW..sB.."])
        plan(d, b, 1, ["979.m.979",
                       "....l....",
                       ".d..d..d.",
                       ".3..3..3.",
                       ".........",
                       ".d..d..d.",
                       ".3..3..3.",
                       "6.......8",
                       "kQz...B.."], face={"Q": "north"})
        put(d, b["S"], [(53, 4, 33, "sign", ("north", ["LOGISTICS"]))])
        for z in range(14, 34):
            d.set(7, 1, z, "smooth_stone")
            d.set(53, 1, z, "smooth_stone")
    if L >= 5:
        # ---- Visitor Centre: gift shop lobby, seed exhibition, auditorium, offices, roof-level cafe
        b = building(d, 22, 40, 38, 50, 5, door="west", ladder=(37, 41, "south"), pal=7)
        plan(d, b, 0, ["7z7z7z7z7z7.9..",
                       "...............",
                       "..cec.....cdc..",
                       "...............",
                       ".....l.....l...",
                       "..B.B.....B.B..",
                       "...............",
                       "..4T2.....4T2..",
                       "a.............a"])
        plan(d, b, 1, ["9.9.9.9.9.9.9..",
                       "...............",
                       ".eee.iii.ggg...",
                       "...............",
                       ".......l.......",
                       ".ggg.eee.iii...",
                       "...............",
                       "6.............8",
                       "a.....Q.....a.."], face={"Q": "north"})
        plan(d, b, 2, ["...............",
                       "....2.2.2.2....",
                       "....2.2.2.2....",
                       "....2.2.2.2....",
                       ".Q..........l..",
                       "....2.2.2.2....",
                       "....2.2.2.2....",
                       "....2.2.2.2....",
                       "a.............a"], face={"Q": "east"})
        plan(d, b, 3, ["979.m.979.979..",
                       "...............",
                       ".d..d..d..d..d.",
                       ".3..3..3..3..3.",
                       "......l........",
                       ".d..d..d..d..d.",
                       ".3..3..3..3..3.",
                       "...............",
                       "kQz.....B...b.."], face={"Q": "north"})
        plan(d, b, 4, ["KcrecC.........",
                       "...............",
                       "4T2..4T2..4T2..",
                       "...............",
                       ".....l....l....",
                       "4T2..4T2..4T2..",
                       "...............",
                       "...............",
                       "z.....9.9....z."], face={"K": "south"})
        put(d, b["S"], [(21, 4, 45, "sign", ("west", ["VISITOR", "CENTRE"]))])
        for z in range(30, 52):
            d.set(20, 1, z, "smooth_stone")
        for x, z in ((1, 18), (59, 18), (1, 50), (59, 50), (44, 52)):
            tree(d, x, z, h=5, log="birch_log", leaves="birch_leaves", r=2)
        for x in (40, 43, 46):
            d.set(x, 2, 47, "smooth_quartz")
            d.set(x, 3, 47, "sea_lantern")
        # solar arrays on the lab and logistics roofs (three rows each inside the parapets)
        for (xa, xb), zs in (((3, 11), (36, 38, 40, 42)), ((49, 57), (36, 38, 40, 42)), ((49, 57), (7, 9, 11))):
            for z in zs:
                for x in range(xa, xb + 1):
                    d.set(x, 12, z, "daylight_detector[inverted=false,power=0]")
    connect_walls(d)
    return d


# ----------------------------------------------------------------------------------------------- material tiers
EARLY_SWAP = {"smooth_quartz_slab": "smooth_stone_slab", "smooth_quartz_stairs": "polished_diorite_stairs",
              "smooth_quartz": "smooth_stone", "quartz_block": "calcite", "quartz_pillar": "white_concrete",
              "quartz_bricks": "calcite", "polished_blackstone": "polished_deepslate",
              "prismarine_bricks": "cyan_terracotta", "polished_blackstone_wall": "polished_deepslate_wall"}


def early_materials(d, L):
    """Levels 1-3 build with common stone / concrete; quartz, blackstone and prismarine stay for levels 4-5.
    Sea lanterns become glowstone on L1-2 (L3 keeps a few as accents)."""
    if L >= 4:
        return d
    bp = d.bp
    for x, y, z, st in list(bp.blocks()):
        if st == AIR:
            continue
        name, _, props = st.partition("[")
        n = name.split(":")[-1]
        new = EARLY_SWAP.get(n)
        if new is None and n == "sea_lantern" and L <= 2:
            new = "glowstone"
        if new is None:
            continue
        if n == "quartz_pillar":
            props = ""
        bp.grid[y][z][x] = f"minecraft:{new}" + (f"[{props}" if props else "")
    return d


_gbn, _rgn, _gbwn, _rgwn = gb_neoterra, rg_neoterra, gbw_neoterra, rgw_neoterra


def gb_neoterra(rel, L):
    return early_materials(_gbn(rel, L), L)


def rg_neoterra(rel, L):
    return early_materials(_rgn(rel, L), L)


def gbw_neoterra(rel, L):
    return early_materials(_gbwn(rel, L), L)


def rgw_neoterra(rel, L):
    return early_materials(_rgwn(rel, L), L)
