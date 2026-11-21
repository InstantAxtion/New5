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


def river(d, x1, x2, bed=("gravel", "clay", "sand"), weir="mossy_stone_bricks", lily=0):
    """River channel along z between x1..x2: water in the ground layer, riverbed below, low weirs at the plot ends
    so the water stays inside the plot."""
    for x in range(x1, x2 + 1):
        for z in range(d.sz):
            d.set(x, 0, z, "structurize:blocksolidsubstitution")
            d.set(x, 1, z, weir if z in (0, d.sz - 1) else WATER)
    if lily:
        import random
        rnd = random.Random(lily)
        for _ in range(lily):
            x, z = rnd.randint(x1, x2), rnd.randint(2, d.sz - 3)
            if d.get(x, 1, z).startswith("minecraft:water") and d.air(x, 2, z):
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
    river(d, 9, 23, lily=6 if L >= 3 else 0)
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
          lily=0)
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
        for x in range(11, 22):
            if x % 3 == 1:
                d.set(x, 2, 2, "lily_pad") if d.get(x, 1, 2).startswith("minecraft:water") else None
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
    river(d, 10, 22, bed=("sand", "gravel", "clay"), weir="smooth_stone", lily=0)
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
    return {"Hearthwood": gb_hearthwood, "Cascadia": gb_cascadia, "Neoterra": gb_neoterra}[pack](rel, L)


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
        if z % 3 == 0:
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
        for x in range(x1 + 1, x2):
            for z in range(z1 + 1, z2):
                if x != 5 and (x + z) % 2 == 0:
                    d.set(x, 2, z, ("wheat[age=7]", "carrots[age=5]", "potatoes[age=7]", "beetroots[age=3]")[(x + z) % 4])
                    d.set(x, 1, z, "farmland[moisture=7]")
                elif x != 5:
                    d.set(x, 1, z, "farmland[moisture=7]")
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
    return {"Hearthwood": rg_hearthwood, "Cascadia": rg_cascadia, "Neoterra": rg_neoterra}[pack](rel, L)


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


def frontage(d, x1, z1, x2, z2, door, dcell, S):
    """Front garden on the door side: flower bed with a low fence/hedge edge, paved walk to the door."""
    ox, oz = DIRS[door]
    flowers = S["flowers"]
    cells = [(x, z1 - 1) for x in range(x1, x2 + 1)] if door == "north" else \
        [(x, z2 + 1) for x in range(x1, x2 + 1)] if door == "south" else \
        [(x1 - 1, z) for z in range(z1, z2 + 1)] if door == "west" else [(x2 + 1, z) for z in range(z1, z2 + 1)]
    for i, (x, z) in enumerate(cells):
        if abs(x - dcell[0]) + abs(z - dcell[1]) <= 2:
            if d.bp.inside(x, 1, z):
                d.set(x, 1, z, S["path"] if d.pack != "Neoterra" else ("smooth_stone" if i % 2 else "polished_andesite"))
            continue
        if not d.bp.inside(x, 2, z) or not d.air(x, 2, z):
            continue
        g = d.get(x, 1, z)
        if not any(k in g for k in ("grass_block", "dirt", "moss", "gravel", "podzol")):
            continue
        d.set(x, 1, z, "grass_block[snowy=false]" if d.pack != "Neoterra" else "moss_block")
        d.set(x, 2, z, flowers[(x + z) % len(flowers)] if (x + z) % 3 else
              ("potted_azalea_bush" if d.pack == "Neoterra" else "rose_bush[half=lower]"))
        if "rose_bush" in d.get(x, 2, z) and d.air(x, 3, z):
            d.set(x, 3, z, "rose_bush[half=upper]")
    # walk: patterned paving from the door outward two cells
    for k in range(1, 3):
        x, z = dcell[0] + ox * k, dcell[1] + oz * k
        if d.bp.inside(x, 1, z) and d.air(x, 2, z):
            d.set(x, 1, z, (S["path"], "cobblestone" if d.pack != "Neoterra" else "polished_andesite")[k % 2])

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


def place_item(d, kind, x, y, z, face, S):
    """One wall-side furnishing (face = direction into the room). Returns True if placed."""
    wood = S["wood"]
    top = f"{S['counter']}[type=top,waterlogged=false]"
    if kind == "barrel":
        d.set(x, y, z, "barrel[facing=up,open=false]")
        d.set(x, y + 1, z, _pot(face))
    elif kind == "barrels":
        d.set(x, y, z, "barrel[facing=up,open=false]")
        d.set(x, y + 1, z, f"barrel[facing={face},open=false]")
    elif kind == "sacks":
        d.set(x, y, z, "white_wool")
        d.set(x, y + 1, z, "brown_carpet")
    elif kind == "hay":
        d.set(x, y, z, "hay_block[axis=y]")
        d.set(x, y + 1, z, "hay_block[axis=x]")
    elif kind == "shelf":
        d.set(x, y, z, _shelf(face))
        d.set(x, y + 1, z, _shelf(face))
        d.set(x, y + 2, z, "potted_fern" if (x + z) % 2 else "candle[candles=2,lit=false,waterlogged=false]")
    elif kind == "books":
        d.set(x, y, z, "bookshelf")
        d.set(x, y + 1, z, "bookshelf")
    elif kind == "lectern":
        d.set(x, y, z, f"lectern[facing={face},has_book=false,powered=false]")
    elif kind in ("cartography_table", "crafting_table", "fletching_table", "smithing_table"):
        d.set(x, y, z, kind)
        d.set(x, y + 1, z, "candle[candles=1,lit=false,waterlogged=false]")
    elif kind in ("furnace", "smoker", "blast_furnace"):
        d.set(x, y, z, f"{kind}[facing={face},lit=false]")
        d.set(x, y + 1, z, S["chim"] or "polished_andesite")
    elif kind == "cauldron":
        d.set(x, y, z, "water_cauldron[level=3]")
    elif kind == "counter":
        d.set(x, y, z, top)
        d.set(x, y + 1, z, _pot(face) if (x + z) % 3 == 0 else
              ("candle[candles=3,lit=false,waterlogged=false]" if (x + z) % 3 == 1 else "potted_red_tulip"))
    elif kind == "brewing":
        d.set(x, y, z, top)
        d.set(x, y + 1, z, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
    elif kind in ("loom", "stonecutter", "grindstone", "anvil"):
        st = {"loom": f"loom[facing={face}]", "stonecutter": f"stonecutter[facing={face}]",
              "grindstone": f"grindstone[face=floor,facing={face}]", "anvil": f"anvil[facing={face}]"}[kind]
        d.set(x, y, z, st)
    elif kind == "bed":
        dx, dz = DIRS[face]
        if not d.air(x + dx, y, z + dz):
            return False
        d.set(x, y, z, f"{S.get('bedc', 'red') if d.pack != 'Neoterra' else 'cyan'}_bed[facing={OPPD[face]},occupied=false,part=head]")
        d.set(x + dx, y, z + dz, f"{'red' if d.pack == 'Hearthwood' else 'brown' if d.pack == 'Cascadia' else 'cyan'}"
                                 f"_bed[facing={OPPD[face]},occupied=false,part=foot]")
        d.set(x, y, z, f"{'red' if d.pack == 'Hearthwood' else 'brown' if d.pack == 'Cascadia' else 'cyan'}"
                       f"_bed[facing={OPPD[face]},occupied=false,part=head]")
    elif kind == "nightstand":
        d.set(x, y, z, top)
        d.set(x, y + 1, z, "lantern[hanging=false,waterlogged=false]")
    elif kind == "plant":
        d.set(x, y, z, ("potted_azalea_bush", "potted_fern", "potted_bamboo", "potted_red_tulip")[(x * 3 + z) % 4])
    elif kind == "pot":
        d.set(x, y, z, _pot(face))
    elif kind == "keg":
        d.set(x, y, z, f"barrel[facing={'east' if face in ('north', 'south') else 'north'},open=false]")
        d.set(x, y + 1, z, top)
    elif kind == "bench":
        d.set(x, y, z, stair(f"{wood}_stairs", OPPD[face]))
    else:
        return False
    return True


class Room:
    """Hand layout helper for one storey of a building(): local frame u (along the door wall, from the hearth
    side toward the ladder side via A()/O()) and v (depth from the door row). Cells that must stay clear (door
    approach, ladder, hearth front) are refused."""

    def __init__(self, d, fr, yb, S, ground):
        self.d, self.fr, self.yb, self.S = d, fr, yb, S
        W, D = fr["Wd"], fr["Dd"]
        self.W, self.D = W, D
        res = set()
        if ground:
            res |= {(fr["du"], 0), (fr["du"], 1)}
            if fr["hearth"]:
                hu, hv = fr["hearth"]
                res |= {(hu, hv), (hu, hv - 1), (hu, hv + 1), (hu + fr["sa"], hv)}
        if fr["n"] > 1:
            res |= {(fr["ul"], D - 1), (fr["ul"], D - 2), (fr["ul"] - fr["sa"], D - 2)}
        self.res = res

    def A(self, k):
        return self.fr["ua"] + self.fr["sa"] * k

    def O(self, k):
        return self.fr["ul"] - self.fr["sa"] * k

    @property
    def fa(self):                                          # facing into the room from the main side wall
        return "u+" if self.fr["sa"] == 1 else "u-"

    @property
    def fo(self):
        return "u-" if self.fr["sa"] == 1 else "u+"

    def ok(self, u, v):
        if not (0 <= u < self.W and 0 <= v < self.D) or (u, v) in self.res:
            return False
        x, z = self.fr["to_w"](u, v)
        return self.d.air(x, self.yb, z) and self.d.air(x, self.yb + 1, z)

    def open_next(self, u, v):
        for nu, nv in ((u + 1, v), (u - 1, v), (u, v + 1), (u, v - 1)):
            if 0 <= nu < self.W and 0 <= nv < self.D:
                x, z = self.fr["to_w"](nu, nv)
                if self.d.air(x, self.yb, z) and self.d.air(x, self.yb + 1, z):
                    return True
        return False

    def put(self, u, v, item, face):
        fu, fv = {"front": (0, -1), "back": (0, 1), "u+": (1, 0), "u-": (-1, 0)}[face]
        if not self.ok(u, v):
            return False
        if 0 <= u + fu < self.W and 0 <= v + fv < self.D:
            fx, fz = self.fr["to_w"](u + fu, v + fv)
            if not self.d.air(fx, self.yb, fz):
                return False
        elif not self.open_next(u, v):
            return False
        x, z = self.fr["to_w"](u, v)
        if item == "bed":
            fu, fv = {"front": (0, -1), "back": (0, 1), "u+": (1, 0), "u-": (-1, 0)}[face]
            if not self.ok(u + fu, v + fv):
                return False
        return place_item(self.d, item, x, self.yb, z, self.fr["ldir"][face], self.S)

    def chair(self, u, v, back):
        if not self.ok(u, v):
            return
        x, z = self.fr["to_w"](u, v)
        self.d.set(x, self.yb, z, stair(f"{self.S['wood']}_stairs", self.fr["ldir"][back]))

    def table(self, u, v, top=None):
        if not self.ok(u, v):
            return
        x, z = self.fr["to_w"](u, v)
        self.d.set(x, self.yb, z, f"{self.S['wood']}_fence")
        self.d.set(x, self.yb + 1, z, top or f"{self.S['wood']}_pressure_plate[powered=false]")

    def rug(self, u1, v1, u2, v2):
        for u in range(min(u1, u2), max(u1, u2) + 1):
            for v in range(min(v1, v2), max(v1, v2) + 1):
                if 0 <= u < self.W and 0 <= v < self.D:
                    x, z = self.fr["to_w"](u, v)
                    if self.d.air(x, self.yb, z):
                        edge = u in (u1, u2) or v in (v1, v2)
                        self.d.set(x, self.yb, z, self.S["rug"][0 if edge else 1])

    def lamp(self, u, v):
        x, z = self.fr["to_w"](u, v)
        top = self.yb + 3
        if not self.d.air(x, top, z):
            return
        yy = top + 1
        while self.d.bp.inside(x, yy, z) and self.d.air(x, yy, z) and yy < top + 6:
            yy += 1
        for y in range(top + 1, yy):
            self.d.set(x, y, z, "chain[axis=y,waterlogged=false]")
        self.d.set(x, top, z, lantern(True))

    def wall_banner(self, u, v, face, color):
        x, z = self.fr["to_w"](u, v)
        if self.d.air(x, self.yb + 2, z):
            self.d.set(x, self.yb + 2, z, f"{color}_wall_banner[facing={self.fr['ldir'][face]}]")


# ---- one layout per room use: fixed places relative to the walls, door, hearth and ladder
def _back(r):                                          # the "u" side the main wall is on
    return "u-" if r.fr["sa"] == 1 else "u+"


def lay_home(r, ground):
    """Bedroom: beds with their heads on the back wall and nightstands between them, a two-high wardrobe on the
    main wall, a writing desk with chair on the ladder side, a reading corner (two armchairs and a side table) by
    the front wall, a rug in the middle and a light over it."""
    D, W = r.D, r.W
    for k in range(0, W - 2, 2):
        r.put(r.A(k), D - 1, "bed", "front")
        r.put(r.A(k + 1), D - 1, "nightstand", "front")
    r.put(r.A(0), 1, "shelf", r.fa)
    r.put(r.A(0), 2, "shelf", r.fa) if D >= 6 else None
    r.put(r.O(0), 2, "counter", r.fo)
    r.chair(r.O(1), 2, _back(r))
    r.put(r.O(0), 1, "barrel", r.fo)
    r.put(r.O(0), 0, "plant", "back")
    r.put(r.A(0), 0, "plant", "back")
    r.chair(r.A(1), 0, "front")
    if r.ok(r.A(2), 0):
        x, z = r.fr["to_w"](r.A(2), 0)
        r.d.set(x, r.yb, z, f"{r.S['counter']}[type=top,waterlogged=false]")
        r.d.set(x, r.yb + 1, z, "candle[candles=2,lit=false,waterlogged=false]")
    r.chair(r.A(3), 0, "front")
    r.rug(W // 2 - 1, D // 2 - 1, W // 2 + 1, D // 2)
    r.wall_banner(r.A(1), D - 1, "front", "red" if r.d.pack == "Hearthwood" else "green")
    r.lamp(W // 2, D // 2)
    if W >= 9:
        r.lamp(r.A(1), D - 3)


def lay_kitchen(r, ground):
    """Kitchen: cooking range along the back wall (smoker, oven, worktop, sink, larder barrels), pantry on the
    ladder side, a dining table with chairs on both long sides in the middle, the hearth on the main side."""
    D, W = r.D, r.W
    run = ("smoker", "furnace", "counter", "cauldron", "counter", "barrel", "counter", "barrels", "counter")
    for k in range(W):
        r.put(r.A(k), D - 1, run[k % len(run)], "front")
    r.put(r.O(0), 1, "barrels", r.fo)
    r.put(r.O(0), 2, "sacks", r.fo)
    r.put(r.A(0), 0, "pot", "back")
    hv = D // 2
    n = max(1, min(3, W - 6))
    for i in range(n):
        tu = r.A(3 + i)
        r.table(tu, hv, "candle[candles=3,lit=false,waterlogged=false]" if i == 0 else None)
        r.chair(tu, hv - 1, "front")
        r.chair(tu, hv + 1, "back")
    r.lamp(r.A(3), hv)
    r.lamp(r.A(1), D - 2)


def lay_inn(r, ground):
    """Taproom: kegs and a smoker on the back wall, a settle facing the fire, a bar counter with stools on the
    ladder side, tables for four along the front."""
    D, W = r.D, r.W
    for k, it in enumerate(("keg", "keg", "barrel", "smoker", "keg", "keg", "barrel", "keg", "keg")):
        r.put(r.A(k), D - 1, it, "front")
    hv = D // 2
    for dv in (0, -1):
        if r.ok(r.A(2), hv + dv):
            x, z = r.fr["to_w"](r.A(2), hv + dv)
            r.d.set(x, r.yb, z, stair(f"{r.S['wood']}_stairs", r.fr["ldir"][r.fo]))
    for v in range(1, min(4, D - 2)):
        r.put(r.O(1), v, "counter", r.fa)
        r.chair(r.O(2), v, _back(r))
    for tu in range(r.A(4), r.O(3) + (1 if r.fr["sa"] == 1 else -1), 3 * r.fr["sa"]):
        r.table(tu, 1)
        r.chair(tu, 0, "front")
        r.chair(tu, 2, "back")
    r.put(r.A(0), 0, "plant", "back")
    r.lamp(W // 2, hv)
    r.lamp(r.O(1), 2)


def lay_office(r, ground):
    """Office: bookcases along the back wall with the head clerk's desk in front of them, rows of desks (desk +
    chair) across the room, lectern, records and map table on the ladder side, an armchair by the fire."""
    D, W = r.D, r.W
    for k in range(W - 2):
        r.put(r.A(k), D - 1, "shelf" if k % 2 == 0 else "books", "front")
    r.put(r.A(1), D - 2, "counter", "front")
    r.chair(r.A(1), D - 3, "front") if D >= 7 else None
    r.put(r.O(0), 1, "lectern", r.fo)
    r.put(r.O(0), 2, "books", r.fo)
    r.put(r.O(0), 0, "cartography_table", "back")
    r.put(r.A(0), 0, "plant", "back")
    if r.fr["hearth"] and ground:
        r.chair(r.A(2), D // 2, "u+" if r.fr["sa"] == 1 else "u-")
    else:
        r.put(r.A(0), 1, "books", r.fa)
        r.put(r.A(0), 2, "plant", r.fa)
    if D >= 7:                                         # desk pods: desk with the chair on its door side
        for v in range(3, D - 3, 3):
            for k in range(3, W - 2, 3):
                r.put(r.A(k), v + 1, "counter", "front")
                r.chair(r.A(k), v, "front")
    r.rug(r.A(1), 1, r.A(2), D - 4)
    r.lamp(W // 2, D // 2)
    if W >= 9:
        r.lamp(r.A(1), 2)
        r.lamp(r.O(2), D - 3)


def lay_shop(r, ground):
    """Shop: sales counter across the room (gap at the door aisle), stock shelves and barrels on the back wall,
    sacks and a display barrel by the entrance."""
    D = r.D
    if D >= 5:
        for u in range(r.W):
            if u != r.fr["du"]:
                r.put(u, 2, "counter", "front")
    for k, it in enumerate(("shelf", "barrels", "shelf", "sacks", "shelf", "barrels", "shelf")):
        r.put(r.A(k), D - 1, it, "front")
    r.put(r.A(0), 0, "barrel", "back")
    r.put(r.O(0), 0, "sacks", "back")
    r.put(r.A(0), 1, "pot", r.fa)
    for v in range(4, D - 2, 3):                       # display stands behind the counter
        for k in range(1, r.W - 2, 3):
            r.put(r.A(k), v, "counter", "front")
            r.put(r.A(k + 1), v, "barrel", "front")
    r.lamp(r.W // 2, 1)
    r.lamp(r.W // 2, D - 2)


def lay_store(r, ground, granary=False):
    """Storehouse: shelving bays down both side walls (barrels stacked, sacks), bulk goods on the back wall,
    clear aisle in the middle."""
    D = r.D
    side = ("sacks", "hay", "sacks", "barrels", "hay", "sacks", "hay") if granary else \
        ("barrels", "sacks", "barrels", "barrel", "barrels", "sacks", "barrels")
    for v in range(1, D):
        r.put(r.A(0), v, side[v % len(side)], r.fa)
    for v in range(1, D - 2):
        r.put(r.O(0), v, side[(v + 3) % len(side)], r.fo)
    for k in range(1, r.W - 2):
        r.put(r.A(k), D - 1, ("hay", "sacks", "barrels")[k % 3] if granary else ("barrels", "sacks", "pot")[k % 3],
              "front")
    r.put(r.A(0), 0, "pot", "back")
    for k in range(3, r.W - 3, 3):                     # free-standing rack rows with two-wide aisles
        for v in range(2, D - 2):
            r.put(r.A(k), v, "barrels" if v % 2 else ("sacks" if granary else "barrel"), "front")
    r.lamp(r.W // 2, D // 2)


def lay_lab(r, ground):
    """Laboratory: bench run with brewing stands and a sink on the main side, island benches down the middle,
    reference shelves and lectern on the ladder side, more shelving on the back wall."""
    D, W = r.D, r.W
    for v, it in zip(range(1, D - 1), ("brewing", "counter", "cauldron", "brewing", "counter", "brewing")):
        r.put(r.A(0), v, it, r.fa)
    if D >= 5:
        for k in range(2, W - 2, 3):
            r.put(r.A(k), D // 2, "brewing", "front")
            r.put(r.A(k + 1), D // 2, "counter", "front")
    r.put(r.O(0), 1, "shelf", r.fo)
    r.put(r.O(0), 2, "lectern", r.fo)
    for k in range(1, W - 2):
        r.put(r.A(k), D - 1, ("shelf", "crafting_table", "shelf", "cauldron")[k % 4], "front")
    r.put(r.O(0), 0, "plant", "back")
    r.lamp(r.A(2), 1)
    r.lamp(W // 2, D - 2)


def lay_mill(r, ground):
    """Mill floor: the millstone (grindstone) and stonecutter in the middle, sacks of flour on the main side,
    grain (hay) on the back wall, barrels on the ladder side."""
    D = r.D
    r.put(r.A(2), D // 2, "grindstone", "front")
    r.put(r.A(3), D // 2, "stonecutter", "front")
    for v in range(1, D):
        r.put(r.A(0), v, "sacks" if v % 2 else "hay", r.fa)
    for k in range(1, r.W - 2):
        r.put(r.A(k), D - 1, "hay" if k % 2 else "sacks", "front")
    for v in range(1, D - 2):
        r.put(r.O(0), v, "barrels" if v % 2 else "barrel", r.fo)
    r.lamp(r.W // 2, 1)


def lay_workshop(r, ground):
    """Workshop: workbench, smithing table and grindstone along the main wall, anvil in front, stock barrels on
    the ladder side, timber and sacks on the back wall."""
    D = r.D
    for v, it in zip(range(1, D - 1), ("crafting_table", "smithing_table", "grindstone", "crafting_table")):
        r.put(r.A(0), v, it, r.fa)
    r.put(r.A(2), 2, "anvil", "front")
    for v in range(1, D - 2):
        r.put(r.O(0), v, "barrels", r.fo)
    for k in range(1, r.W - 2):
        r.put(r.A(k), D - 1, ("hay", "barrels", "sacks")[k % 3], "front")
    r.lamp(r.W // 2, D // 2)


LAYOUTS = {"home": lay_home, "kitchen": lay_kitchen, "inn": lay_inn, "office": lay_office, "shop": lay_shop,
           "store": lay_store, "granary": lambda r, g: lay_store(r, g, True), "lab": lay_lab, "mill": lay_mill,
           "workshop": lay_workshop}


def room_layout(d, frame, yb, kind, S, ground):
    LAYOUTS[kind](Room(d, frame, yb, S, ground), ground)


def building(d, x1, z1, x2, z2, kinds, door="south", doorpos=None, y0=2, roof="gable", axis=None, name=None,
             chimney=True, beds_ok=True, pal=0, garden=True):
    """A furnished house-type building in the pack's style. kinds = room kind per storey (ground first).
    pal picks one of the pack's palette variants (walls / framing / roof / shutters) so a street is not one theme."""
    S = dict(STYLE[d.pack])
    S.update(PALS[d.pack][pal % len(PALS[d.pack])])
    S.setdefault("band", "light_gray_concrete")
    pk = d.pack
    n = len(kinds)
    SH = 5
    lx, lz = x2 - x1, z2 - z1
    axis = axis or ("x" if lx >= lz else "z")
    # door cell and its inside cell
    if door in ("north", "south"):
        dpx = doorpos if doorpos is not None else (x1 + x2) // 2
        dz_ = z1 if door == "north" else z2
        dcell, inside = (dpx, dz_), (dpx, dz_ + (1 if door == "north" else -1))
        outside = (dpx, dz_ + (-1 if door == "north" else 1))
    else:
        dpz = doorpos if doorpos is not None else (z1 + z2) // 2
        dx_ = x1 if door == "west" else x2
        dcell, inside = (dx_, dpz), (dx_ + (1 if door == "west" else -1), dpz)
        outside = (dx_ + (-1 if door == "west" else 1), dpz)
    # local room frame: u along the front (door) wall, v = depth from the front row inward
    ix1, ix2, iz1, iz2 = x1 + 1, x2 - 1, z1 + 1, z2 - 1
    if door == "north":
        Wd, Dd = ix2 - ix1 + 1, iz2 - iz1 + 1
        to_w = lambda u, v: (ix1 + u, iz1 + v)
        ldir = {"u+": "east", "u-": "west", "back": "south", "front": "north"}
    elif door == "south":
        Wd, Dd = ix2 - ix1 + 1, iz2 - iz1 + 1
        to_w = lambda u, v: (ix2 - u, iz2 - v)
        ldir = {"u+": "west", "u-": "east", "back": "north", "front": "south"}
    elif door == "west":
        Wd, Dd = iz2 - iz1 + 1, ix2 - ix1 + 1
        to_w = lambda u, v: (ix1 + v, iz2 - u)
        ldir = {"u+": "north", "u-": "south", "back": "east", "front": "west"}
    else:
        Wd, Dd = iz2 - iz1 + 1, ix2 - ix1 + 1
        to_w = lambda u, v: (ix2 - v, iz1 + u)
        ldir = {"u+": "south", "u-": "north", "back": "west", "front": "east"}
    du = next(u for u in range(Wd) if to_w(u, 0) == inside)
    ul = Wd - 1 if du < Wd / 2 else 0                      # ladder in the back corner away from the door
    sa = 1 if ul == Wd - 1 else -1                         # direction from the main (hearth) side toward the ladder
    ua = 0 if ul == Wd - 1 else Wd - 1                     # main furniture side
    lad = to_w(ul, Dd - 1)
    lface = ldir["front"]
    hearth = None
    chim = None
    if chimney and S["chim"] and kinds[0] in ("home", "inn", "kitchen", "office") and Dd >= 5:
        hearth = (ua, Dd // 2)
        chim = to_w(ua - sa, Dd // 2)
    frame = dict(Wd=Wd, Dd=Dd, to_w=to_w, ldir=ldir, du=du, ul=ul, ua=ua, sa=sa, hearth=hearth, n=len(kinds))
    pending = []
    for s, kind in enumerate(kinds):
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
                        if corner or along % 4 == 0:
                            st = f"{S['post']}[axis=y]"
                        elif s == 0 and y == yb:
                            st = S["base"]
                        else:
                            st = S["wall"]
                    elif pk == "Cascadia":
                        st = f"{S['post']}[axis=y]" if corner else \
                            f"{S['wall']}[axis={'x' if z in (z1, z2) else 'z'}]"
                    else:
                        st = S["post"] if corner else (S["wall"] if y != yb + 3 else S["band"])
                    d.set(x, y, z, st)
            # floor beams on the wall line
            if s > 0:
                for x in range(x1, x2 + 1):
                    for z in (z1, z2):
                        d.set(x, yb - 1, z, f"{S['beam']}[axis=x]" if pk != "Neoterra" else S["band"])
                for z in range(z1, z2 + 1):
                    for x in (x1, x2):
                        d.set(x, yb - 1, z, f"{S['beam']}[axis=z]" if pk != "Neoterra" else S["band"])
        if s == 0 and pk == "Cascadia":
            for x in range(x1, x2 + 1):
                for z in range(z1, z2 + 1):
                    if x in (x1, x2) or z in (z1, z2):
                        d.set(x, yb - 1, z, ("cobblestone", "mossy_cobblestone", "andesite")[(x + z) % 3])
        # windows with sills / boxes and shutters
        def wins(cells, out):
            ox, oz = DIRS[out]
            for i, (x, z) in enumerate(cells):
                if i < 1 or i > len(cells) - 2 or (x, z) == chim:
                    continue
                if pk == "Neoterra":
                    if i % 4 == 0:
                        continue
                    for y in (yb + 1, yb + 2):
                        d.set(x, y, z, "light_gray_stained_glass_pane" if s % 2 else "glass_pane")
                    continue
                if i % 3 != 2 or abs(x - dcell[0]) + abs(z - dcell[1]) <= 1 and s == 0:
                    continue
                d.set(x, yb + 1, z, "glass_pane")
                d.set(x, yb + 2, z, "glass_pane")
                if not d.bp.inside(x + ox, yb, z + oz):
                    continue
                if s == 0:
                    if d.air(x + ox, yb, z + oz):
                        d.set(x + ox, yb, z + oz, f"potted_{S['flowers'][(x + z) % 4]}")
                else:
                    d.set(x + ox, yb, z + oz, f"{S['trap']}[facing={out},half=top,open=false,powered=false,waterlogged=false]")
                    d.set(x + ox, yb + 1, z + oz, f"potted_{S['flowers'][(x + z) % 4]}")
                for sx_, sz_ in ((((x - 1, z), (x + 1, z)) if out in ("north", "south") else ((x, z - 1), (x, z + 1)))
                                 if (s == 0 or pk == "Cascadia") else ()):
                    for y in (yb + 1, yb + 2):
                        if d.bp.inside(sx_ + ox, y, sz_ + oz) and d.air(sx_ + ox, y, sz_ + oz):
                            d.set(sx_ + ox, y, sz_ + oz,
                                  f"{S['trap']}[facing={out},half=bottom,open=true,powered=false,waterlogged=false]")
        wins([(x, z1) for x in range(x1, x2 + 1)], "north")
        wins([(x, z2) for x in range(x1, x2 + 1)], "south")
        wins([(x1, z) for z in range(z1, z2 + 1)], "west")
        wins([(x2, z) for z in range(z1, z2 + 1)], "east")
        if hearth and s == 0:
            hx, hz = to_w(*hearth)
            d.set(hx, yb, hz, f"campfire[facing={ldir['u+' if sa == 1 else 'u-']},lit=true,signal_fire=false,waterlogged=false]")
            for y in range(yb + 1, yb + 4):
                d.set(hx, y, hz, S["chim"])
            for dv in (-1, 1):                              # mantel / hearth cheeks
                ex, ez = to_w(hearth[0], hearth[1] + dv)
                d.set(ex, yb, ez, S["chim"])
                d.set(ex, yb + 1, ez, f"{S['chimcap']}[type=bottom,waterlogged=false]")
        if kind == "home" and not beds_ok:
            kind = "office"
        free = None
        pending.append((yb, kind, free))
    top = y0 + n * SH - 1                                  # roof level
    # ladders between storeys
    if n > 1:
        for y in range(y0, y0 + (n - 1) * SH):
            d.set(lad[0], y, lad[1], f"ladder[facing={lface},waterlogged=false]")
    # door
    d.set(dcell[0], y0, dcell[1], AIR)
    d.set(dcell[0], y0 + 1, dcell[1], AIR)
    d.door(dcell[0], y0, dcell[1], door, S["wood"] if pk != "Neoterra" else "birch")
    if d.bp.inside(outside[0], 1, outside[1]):
        d.set(outside[0], 1, outside[1], S["path"])
    ox, oz = DIRS[door]
    side = ((-1, 0), (1, 0)) if door in ("north", "south") else ((0, -1), (0, 1))
    for k, (ax, az) in enumerate(side):
        tx, tz = dcell[0] + ax + ox, dcell[1] + az + oz
        if d.bp.inside(tx, y0 + 2, tz) and d.air(tx, y0 + 2, tz):
            if pk == "Neoterra":
                d.set(tx, y0 + 2, tz, "end_rod[facing=" + door + "]")
            else:
                d.wall_torch(tx, y0 + 2, tz, door)
    if name and d.bp.inside(outside[0], y0 + 2, outside[1]):
        d.sign(outside[0], y0 + 2, outside[1], door, name, S["wood"] if pk != "Neoterra" else "birch",
               glow=pk == "Neoterra", color="cyan" if pk == "Neoterra" else "black")
    if pk == "Neoterra":                                   # door canopy
        for ax in (-1, 0, 1):
            tx = dcell[0] + (ax if door in ("north", "south") else 0) + ox
            tz = dcell[1] + (ax if door in ("east", "west") else 0) + oz
            if d.bp.inside(tx, y0 + 3, tz) and d.air(tx, y0 + 3, tz):
                d.set(tx, y0 + 3, tz, "smooth_quartz_slab[type=top,waterlogged=false]")
    if garden:
        frontage(d, x1, z1, x2, z2, door, dcell, S)
    # roof
    if roof == "flat" or pk == "Neoterra":
        d.fill(x1, top, z1, x2, top, z2, "smooth_quartz")
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if x in (x1, x2) or z in (z1, z2):
                    d.set(x, top + 1, z, S.get("parapet", "white_concrete"))
                    d.set(x, top + 2, z, "smooth_quartz_slab[type=bottom,waterlogged=false]")
                elif (x - x1) % 2 == 1 and z1 + 1 < z < z2 - 1:
                    d.set(x, top + 1, z, "daylight_detector[inverted=false,power=0]")
                elif z in (z1 + 1, z2 - 1) and (x + z) % 3 == 0:
                    d.set(x, top + 1, z, "moss_block")
                    d.set(x, top + 2, z, "azalea")
        for yb, kind, free in pending:
            room_layout(d, frame, yb, kind, S, ground=(yb == y0))
        return top + 2
    ridge = d.gable(x1, z1, x2, z2, top, axis, S["roofst"], S["roofsl"], S["end"], overhang=1)
    if pk == "Hearthwood":                                 # framed gable ends
        mid_a = (z1 + z2) // 2 if axis == "x" else (x1 + x2) // 2
        for y in range(top, ridge):
            for e in ((x1, x2) if axis == "x" else (z1, z2)):
                cx, cz = (e, mid_a) if axis == "x" else (mid_a, e)
                if d.get(cx, y, cz) == "minecraft:calcite":
                    d.set(cx, y, cz, f"{S['post']}[axis=y]")
    if chim:
        cx, cz = chim
        for y in range(y0, ridge + 2):
            if not ("ladder" in d.get(cx, y, cz) or "door" in d.get(cx, y, cz)):
                d.set(cx, y, cz, S["chim"])
        d.set(cx, ridge + 2, cz, f"{S['chimcap']}[type=bottom,waterlogged=false]")
    for yb, kind, free in pending:
        room_layout(d, frame, yb, kind, S, ground=(yb == y0))
    return ridge


def bench_pair(d, x, z, facing, wood, y=2):
    """Outdoor bench of two stair seats (back toward `facing`) with planters at the ends."""
    dx, dz = (1, 0) if facing in ("north", "south") else (0, 1)
    for i in range(2):
        d.set(x + dx * i, y, z + dz * i, stair(f"{wood}_stairs", facing))
    for i in (-1, 2):
        if d.bp.inside(x + dx * i, y, z + dz * i) and d.air(x + dx * i, y, z + dz * i):
            d.set(x + dx * i, y, z + dz * i, "potted_azalea_bush")


def path(d, x1, z1, x2, z2, block, border=None):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for z in range(min(z1, z2), max(z1, z2) + 1):
            d.set(x, 1, z, block)
    if border:
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for z in range(min(z1, z2), max(z1, z2) + 1):
                if (x in (min(x1, x2), max(x1, x2)) and x1 != x2) or (z in (min(z1, z2), max(z1, z2)) and z1 != z2):
                    pass


def flowerbed(d, x1, z1, x2, z2, flowers, soil="grass_block[snowy=false]"):
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if d.air(x, 2, z):
                d.set(x, 1, z, soil)
                d.set(x, 2, z, flowers[(x * 3 + z) % len(flowers)])


def hedge(d, x1, z1, x2, z2, leaves="oak_leaves"):
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if d.air(x, 2, z):
                d.set(x, 2, z, f"{leaves}[distance=1,persistent=true,waterlogged=false]")


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
        if L >= 3 and x % 2 == 0:
            d.set(x, 1, 18, "stone_brick_slab[type=top,waterlogged=false]") if False else None
    # bridge-foot town, a building more per level
    if L >= 2:                                             # toll house by the west gate
        building(d, 4, 11, 10, 17, ["office"], door="south", name=["Toll", "House"], pal=0)
        bench_pair(d, 1, 17, "north", "dark_oak")
        d.set(11, 2, 18, "barrel[facing=up,open=false]")
        d.set(11, 2, 16, "hay_block[axis=y]")
    if L >= 3:                                             # the bridge inn
        building(d, 46, 8, 56, 16, ["inn", "home"], door="south", name=["The", "Ferryman"], pal=1)
        lamppost(d, 45, 17, post="dark_oak_fence")
        for x in (48, 54):
            d.set(x, 2, 18, "barrel[facing=up,open=false]")
        bench_pair(d, 53, 18, "north", "dark_oak")
        hedge(d, 46, 3, 56, 3)
        tree(d, 51, 2, h=4)
    if L >= 4:                                             # water mill on the west bank, cottage behind
        building(d, 13, 32, 20, 39, ["mill", "granary"], door="north", name=["Bridge", "Mill"], chimney=False, pal=2)
        waterwheel(d, 22, 35.5, 3, 2.5)
        building(d, 2, 25, 10, 33, ["kitchen", "home"], door="north", name=["Miller's", "Cottage"], pal=3)
        flowerbed(d, 2, 35, 10, 36, ("poppy", "oxeye_daisy", "cornflower", "allium"))
        for x in range(1, 12):
            d.set(x, 2, 38, "oak_fence")
        for z in (23, 22):
            d.set(6, 1, z, "gravel")
            d.set(16, 1, z + 9, "gravel")
        path(d, 16, 23, 16, 31, "gravel")
    if L >= 5:                                             # guildhall, boathouse, second cottage, gardens
        building(d, 46, 25, 56, 34, ["shop", "office"], door="north", name=["Guild", "Hall"], pal=4)
        building(d, 38, 32, 44, 39, ["store"], door="west", name=["Boat", "House"], chimney=False, pal=5)
        building(d, 2, 1, 10, 8, ["kitchen", "home"], door="south", name=["Bridge", "Cottage"], pal=6)
        flowerbed(d, 47, 36, 56, 37, ("rose_bush[half=lower]", "peony[half=lower]"))
        for x in range(47, 57):
            st = d.get(x, 2, 36).split(":")[1]
            d.set(x, 3, 36, st.replace("lower", "upper"))
            st = d.get(x, 2, 37).split(":")[1]
            d.set(x, 3, 37, st.replace("lower", "upper"))
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
    for x in range(0, d.sx):                              # rail fence along the road edges outside the bridge
        if OX - 1 <= x <= OX + 33:
            continue
        for z in (16, 22):
            if x % 4 == 0:
                d.set(x, 2, z, "spruce_fence") if False else None
    if L >= 2:                                             # ranger & toll station
        building(d, 3, 9, 10, 15, ["office"], door="south", name=["Ranger", "Station"], pal=0)
        lamppost(d, 11, 16, post="spruce_fence")
        d.set(2, 2, 16, "barrel[facing=up,open=false]")
        d.set(1, 2, 16, "hay_block[axis=y]")
        tree(d, 5, 3, h=6, log="spruce_log", leaves="spruce_leaves", r=2)
    if L >= 3:                                             # general store with a porch
        building(d, 48, 7, 58, 15, ["shop", "home"], door="south", name=["General", "Store"], pal=1)
        for x in range(47, 60):
            d.set(x, 1, 16, "spruce_planks")
            d.set(x, 6, 16, stair("dark_oak_stairs", "north"))
        for x in (47, 52, 54, 59):
            for y in range(2, 6):
                d.set(x, y, 16, "spruce_log[axis=y]")
        for x in (49, 57):
            d.set(x, 2, 16, "barrel[facing=up,open=false]")
        d.set(50, 2, 16, stair("spruce_stairs", "north"))
        d.set(56, 2, 16, stair("spruce_stairs", "north"))
    if L >= 4:                                             # sawmill on the river with its wheel, bunkhouse
        building(d, 14, 29, 23, 37, ["mill", "workshop"], door="north", name=["Sawmill"], chimney=False, pal=2)
        waterwheel(d, 25, 33.5, 3, 2.5)
        for z in range(24, 28):                            # log deck
            for x in range(15, 23, 2):
                d.set(x, 2, z, "spruce_log[axis=z]")
            d.set(16, 3, z, "spruce_log[axis=z]")
            d.set(20, 3, z, "spruce_log[axis=z]")
        building(d, 2, 25, 10, 33, ["kitchen", "home"], door="north", name=["Bunk", "House"], pal=3)
        for x in range(1, 12):
            d.set(x, 2, 35, "spruce_fence")
    if L >= 5:                                             # hotel, cabins, firs, lamp posts
        building(d, 48, 25, 58, 35, ["inn", "home", "home"], door="north", name=["Timberline", "Hotel"], pal=4)
        building(d, 38, 30, 45, 37, ["home"], door="west", name=["Cabin"], pal=5)
        for x in range(47, 60):
            d.set(x, 1, 24, "spruce_planks")
            d.set(x, 6, 24, stair("dark_oak_stairs", "south"))
        for x in (47, 52, 54, 59):
            for y in range(2, 6):
                d.set(x, y, 24, "spruce_log[axis=y]")
        building(d, 2, 1, 9, 7, ["workshop"], door="west", name=["Smithy"], chimney=False, pal=0)
        for x, z in ((13, 2), (58, 2), (59, 37), (47, 37)):
            tree(d, x, z, h=7, log="spruce_log", leaves="spruce_leaves", r=2)
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
    if L >= 2:                                             # river cafe pavilion
        building(d, 3, 9, 11, 16, ["shop"], door="south", name=["RIVER", "CAFE"], pal=0)
        for x in (4, 8):
            d.set(x, 2, 17, "birch_fence") if False else None
        for x in range(3, 12, 4):
            d.set(x, 1, 6, "smooth_stone")
            d.table(x, 2, 6, "birch", "post")
            d.chair(x - 1, 2, 6, "west", "birch", sit=False)
            d.chair(x + 1, 2, 6, "east", "birch", sit=False)
    if L >= 3:                                             # transit & bike hub with a terrace
        building(d, 49, 8, 60, 16, ["office"], door="south", name=["TRANSIT", "HUB"], pal=1)
        for x in range(49, 61, 2):
            d.set(x, 2, 6, "iron_bars")
            d.set(x, 2, 5, "smooth_stone_slab[type=bottom,waterlogged=false]")
        for x in (48, 61):
            for z in (3, 17):
                d.set(x, 2, z, "smooth_quartz")
                d.set(x, 3, z, "sea_lantern")
    if L >= 4:                                             # riverside offices and a kayak house
        building(d, 2, 29, 12, 38, ["office", "lab"], door="north", name=["RIVER", "LAB"], pal=2)
        building(d, 40, 35, 47, 42, ["store"], door="west", name=["KAYAK", "HIRE"], pal=3)
        for x in range(2, 13):
            d.set(x, 1, 27, "smooth_stone")
        for z in range(31, 44, 3):
            d.set(39, 1, z, "smooth_stone")
    if L >= 5:                                             # apartment tower, park
        building(d, 50, 29, 60, 39, ["shop", "home", "home", "home", "office"], door="north",
                 name=["SKYLINE", "RESIDENCES"], pal=4)
        for x, z in ((2, 2), (14, 3), (61, 2), (48, 42), (20, 41)):
            tree(d, x, z, h=5, log="birch_log", leaves="birch_leaves", r=2)
        for x in (14, 48):
            for z in (17, 27):
                d.set(x, 2, z, "smooth_quartz")
                d.set(x, 3, z, "sea_lantern")
        flowerbed(d, 50, 41, 60, 42, ("azure_bluet", "white_tulip", "allium", "lily_of_the_valley"), "moss_block")
    connect_walls(d)
    return d


# ----------------------------------------------------------------------------------------------- granaries
def rg_hearthwood(rel, L):
    OX = 14
    big = Design("Hearthwood", rel, (61, 26, 49), gy=1, paving="grass_block[snowy=false]")
    small = core_rg_hearthwood(rel, L)
    paste(big, small, OX, 0)
    d = big
    fl = ("poppy", "oxeye_daisy", "cornflower", "allium")
    for x in range(0, d.sx):                              # farm lane along the street
        for z in (0, 1):
            if d.get(x, 1, z).endswith("grass_block[snowy=false]"):
                d.set(x, 1, z, "dirt_path")
    if L >= 2:                                             # cart shed
        building(d, 2, 4, 11, 11, ["store"], door="south", name=["Cart", "Shed"], chimney=False, pal=3)
        for x in (4, 9):                                   # a hay wain in front
            d.set(x, 2, 14, "oak_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
        d.fill(5, 2, 14, 8, 2, 14, "hay_block[axis=x]")
        d.set(6, 3, 14, "hay_block[axis=x]")
        d.set(10, 2, 14, "oak_fence")
    if L >= 3:                                             # stables with a hayloft
        building(d, 49, 4, 59, 12, ["store", "granary"], door="south", name=["Royal", "Stables"], chimney=False, pal=4)
        for x in range(48, 61):
            d.set(x, 2, 15, "oak_fence") if x % 5 else d.set(x, 2, 15, "oak_fence_gate[facing=south,in_wall=false,open=false,powered=false]")
        d.set(52, 2, 14, "water_cauldron[level=3]")
        d.set(56, 2, 14, "hay_block[axis=y]")
        building(d, 2, 17, 10, 24, ["granary"], door="east", name=["Seed", "Granary"], chimney=False, pal=5)
    if L >= 4:                                             # steward's farmhouse and the malt house behind the barn
        building(d, 2, 28, 12, 37, ["kitchen", "home"], door="north", name=["Steward's", "House"], pal=6)
        flowerbed(d, 2, 25, 12, 26, fl)
        building(d, 48, 28, 58, 37, ["mill", "granary"], door="north", name=["Malt", "House"], pal=7)
        for z in range(23, 28):
            d.set(7, 1, z, "gravel")
            d.set(53, 1, z, "gravel")
        lamppost(d, 13, 27)
        lamppost(d, 47, 27)
    if L >= 5:                                             # bakehouse, tithe clerk's office, walled kitchen garden
        building(d, 17, 30, 27, 38, ["kitchen", "store"], door="north", name=["Bake", "House"], pal=8)
        building(d, 33, 30, 43, 38, ["office", "home"], door="north", name=["Tithe", "Office"], pal=9)
        for x in range(14, 47):
            for z in (41, 47):
                d.set(x, 2, z, "cobblestone_wall")
        for z in range(41, 48):
            d.set(14, 2, z, "cobblestone_wall")
            d.set(46, 2, z, "cobblestone_wall")
        d.set(30, 2, 41, AIR)
        for x in range(16, 45):
            for z in range(43, 46):
                if x % 4 == 0:
                    d.set(x, 1, z, "gravel")
                else:
                    d.set(x, 1, z, "farmland[moisture=7]")
                    d.set(x, 2, z, ("wheat[age=7]", "carrots[age=7]", "potatoes[age=7]", "beetroots[age=3]")[(x // 4) % 4])
        for x in (16, 44):
            tree(d, x, 39, h=4, leaves="oak_leaves", r=1)
        building(d, 49, 40, 58, 47, ["kitchen", "home", "home"], door="west", name=["Alms", "House"], pal=10)
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
    if L >= 2:                                             # scale house
        building(d, 2, 6, 10, 12, ["office"], door="north", name=["Scale", "House"], pal=3)
        for x in range(3, 10):
            d.set(x, 1, 4, "smooth_stone")
    if L >= 3:                                             # warehouse with a loading dock on the siding
        building(d, 45, 6, 55, 14, ["store", "store"], door="north", name=["Feed &", "Seed"], chimney=False, pal=4)
        for x in range(45, 56):
            d.set(x, 1, 5, "spruce_planks")
            d.set(x, 1, 4, "spruce_planks")
        for x in (46, 48, 53):
            d.set(x, 2, 4, "barrel[facing=up,open=false]")
        d.set(54, 2, 4, "white_wool")
        d.set(54, 3, 4, "white_wool")
    if L >= 4:                                             # feed mill and bunkhouse behind
        building(d, 2, 33, 12, 42, ["mill", "workshop"], door="north", name=["Feed", "Mill"], chimney=False, pal=5)
        building(d, 44, 33, 54, 42, ["kitchen", "home"], door="north", name=["Bunk", "House"], pal=6)
        for x, z in ((1, 30), (55, 30), (28, 48)):
            tree(d, x, z, h=6, log="spruce_log", leaves="spruce_leaves", r=2)
    if L >= 5:                                             # co-op hall and grain sheds
        building(d, 18, 36, 30, 46, ["shop", "office", "home"], door="north", name=["Grain", "Co-op Hall"], pal=7)
        building(d, 35, 38, 42, 46, ["granary", "store"], door="west", name=["Grain", "Shed"], chimney=False, pal=8)
        building(d, 4, 45, 12, 50, ["store"], door="east", name=["Tool", "Shed"], chimney=False, pal=9)
        for x in (16, 32):
            lamppost(d, x, 34, post="spruce_fence")
        for x, z in ((14, 48), (43, 48), (55, 48)):
            tree(d, x, z, h=7, log="spruce_log", leaves="spruce_leaves", r=2)
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
    if L >= 2:                                             # security gatehouse
        building(d, 2, 7, 11, 14, ["office", "office"], door="north", name=["SECURITY", "GATE"], pal=3)
        for x in range(1, 13, 3):
            d.set(x, 2, 5, "smooth_quartz")
            d.set(x, 3, 5, "sea_lantern")
    if L >= 3:                                             # genetics lab
        building(d, 48, 5, 58, 13, ["lab", "office"], door="north", name=["GENE", "LAB"], pal=4)
        flowerbed(d, 48, 15, 58, 16, ("azure_bluet", "white_tulip", "allium"), "moss_block")
    if L >= 4:                                             # greenhouse research wing and logistics centre
        building(d, 2, 34, 12, 44, ["lab", "lab"], door="north", name=["CROP", "RESEARCH"], pal=5)
        building(d, 48, 34, 58, 44, ["store", "office"], door="north", name=["LOGISTICS"], pal=6)
        for z in range(14, 34):
            d.set(7, 1, z, "smooth_stone")
            d.set(53, 1, z, "smooth_stone")
    if L >= 5:                                             # visitor centre tower and park
        building(d, 22, 40, 38, 50, ["shop", "office", "office", "office", "office"], door="west",
                 name=["VISITOR", "CENTRE"], pal=7)
        for z in range(30, 52):
            d.set(20, 1, z, "smooth_stone")
        for x, z in ((1, 18), (59, 18), (1, 50), (59, 50), (44, 52)):
            tree(d, x, z, h=5, log="birch_log", leaves="birch_leaves", r=2)
        for x in range(40, 47, 3):
            d.set(x, 2, 47, "smooth_quartz")
            d.set(x, 3, 47, "sea_lantern")
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
