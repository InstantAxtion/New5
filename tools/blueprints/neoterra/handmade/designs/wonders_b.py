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
            d.set(x, 0, z, bed[(x * 7 + z * 3) % len(bed)])
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


def gb_hearthwood(rel, L):
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
            d.set(15, yb + 1, zb2 + 2, "dark_oak_slab[type=top,waterlogged=false]") if False else None
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
        for x, z in ((8, 2), (24, 3), (8, 19), (24, 20)):
            d.set(x, 2, z, "sugar_cane") if False else None
        for z in list(range(2, 6)) + list(range(17, 21)):
            for x in (9, 23):
                if z % 2 == 0:
                    d.set(x, 1, z, "grass_block[snowy=false]")
                    d.set(x, 2, z, "sugar_cane")
    if L >= 3:
        tree(d, 3, 2, h=4, leaves="oak_leaves")
        tree(d, 29, 20, h=4, leaves="oak_leaves")
        for z in (zr1 - 4, zr2 + 4):
            lamppost(d, 7, z) if False else None
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


def gb_cascadia(rel, L):
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
                    d.set(x, Y + H - 2, zr1 - 1, lantern()) if False else None
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
        d.set(X1 + 1, Y, zg, AIR) if False else None
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
    for x, f in ((0, "west"), (W - 1, "east")):
        d.sign(x if False else (1 if f == "west" else W - 2) + (-1 if f == "west" else 1), 5, 4, f,
               ["CASCADIA", "CROSSING"], "spruce") if False else None
    for f, x in (("west", 0), ("east", W - 1)):
        for z in range(3, 6):
            d.set(x, 5, z, "spruce_planks")
        d.sign(x + (-1 if f == "west" else 1), 5, 4, f, ["CASCADIA", "CROSSING"], "spruce") if False else None
    d.hut(3, 1, 0, "south")
    d.set(2, 1, 0, "barrel[facing=up,open=false]")
    d.set(4, 1, 0, "spruce_slab[type=bottom,waterlogged=false]") if False else None
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


def gb_neoterra(rel, L):
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
                d.set(x0 + 2, 2, z, "potted_bamboo") if False else None
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
                d.set(x, 3, z, "cyan_banner[rotation=0]") if False else d.set(x, 3, z, "end_rod[facing=up]")
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
