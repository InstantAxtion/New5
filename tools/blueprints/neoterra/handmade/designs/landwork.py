"""
Land-work huts: farmer, fisherman, plantation, miner, nether worker - each grows from a small working core (L1) into
a complex of purpose-built, furnished buildings (L5), built with the decorated-building kit below (bld / run / porch /
yard decor). Every type has its own palette per pack (see d.palette and the per-building pal= overrides).

Farmer      Hearthwood Cotswold farmhouse (sandstone, red tile) -> tool shed, threshing barn, stable range, dovecote,
            granary, workers' cottage, orchard.  Cascadia log homestead -> tool shed, red gambrel barn, coop, corral,
            machine shed, stave silo, windmill, bunkhouse, creamery.  Neoterra agri hub (white/birch/lime, green roofs)
            -> garage, hydroponic greenhouse, vertical-farm tower, solar canopy, seed bank.
Fisherman   Neoterra harbour master (white/cyan) -> deck, fish market, cold store, boat hall, lighthouse.  Hearthwood
            blue-washed cottage (blue slate) -> smokehouse, market hall, boathouse, net-mender's cottage, harbourmaster's
            house, harbour light, chandlery.  Cascadia birch fish camp (green metal roofs) -> smoke shack, ice house,
            cannery, bunkhouse, lookout.
Plantation  Neoterra agri lab (grey/orange) -> greenhouse, research tower, packing hall.  Hearthwood walled kitchen
            garden (white plaster, rose tile) -> glasshouses, potting yard, head gardener's cottage, bothy, vinery,
            orangery, apple store.  Cascadia farm stand (dark oak, mustard, red cedar) -> cane press, gambrel barn,
            sugar mill with water wheel, water tower, cutters' cabins, mess hall.
Miner       Hearthwood count house + Cornish engine house and stack -> boiler house, dressing floor, ore bins, miners'
            dry, powder magazine, smithy, cottages, spoil heap.  Cascadia log hoist house + timber head-frame -> tipple,
            assay office, bunkhouse, stamp mill, blacksmith, lamp house, cookhouse.  Neoterra winding tower + station
            (grey/deepslate/yellow) -> processing hall, ore silos, control tower, admin block, solar parking.
Netherworker  shrine around the portal (L1) -> narthex and vestry (L2) -> great hall taking the cluster's gallery as
            its front, south annex (L3) -> east library/lab wing (L4) -> west refectory wing, watch tower, ember garden.
"""
from hm import Design, design, AIR, D4, OPP, CW


# ------------------------------------------------------------------------------------------------- helpers
def stair(b, facing, half="bottom", shape="straight"):
    b = b if b.endswith("_stairs") else b + "_stairs"
    return f"{b}[facing={facing},half={half},shape={shape},waterlogged=false]"


def slab(b, t="bottom"):
    b = b if b.endswith("_slab") else b + "_slab"
    return f"{b}[type={t},waterlogged=false]"


def logb(b, axis="y"):
    return f"{b}[axis={axis}]"


def trap(b, facing, half="top", open_=False):
    return f"{b}_trapdoor[facing={facing},half={half},open={'true' if open_ else 'false'},powered=false,waterlogged=false]"


def rail(shape):
    return f"rail[shape={shape},waterlogged=false]"


CHAIN = "chain[axis=y,waterlogged=false]"
HOPPER = "hopper[enabled=true,facing=down]"


def walls(d, x1, z1, x2, z2, y1, y2, mat):
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            d.set(x, y, z1, mat)
            d.set(x, y, z2, mat)
        for z in range(z1, z2 + 1):
            d.set(x1, y, z, mat)
            d.set(x2, y, z, mat)


def posts(d, pts, y1, y2, mat):
    for x, z in pts:
        for y in range(y1, y2 + 1):
            d.set(x, y, z, mat)


def ladder(d, x, z, y1, y2, facing):
    for y in range(y1, y2 + 1):
        d.set(x, y, z, f"ladder[facing={facing},waterlogged=false]")


def track(d, pts, y):
    """Rails through a list of cells (orthogonal neighbours); shapes worked out from the neighbours."""
    for i, (x, z) in enumerate(pts):
        nb = []
        for j in (i - 1, i + 1):
            if 0 <= j < len(pts):
                nb.append((pts[j][0] - x, pts[j][1] - z))
        dirs = {(0, -1): "n", (0, 1): "s", (1, 0): "e", (-1, 0): "w"}
        ds = sorted(dirs[v] for v in nb)
        if len(ds) == 2 and ds[0] != ds[1] and {"n", "s"} != set(ds) and {"e", "w"} != set(ds):
            m = {frozenset("se"): "south_east", frozenset("sw"): "south_west", frozenset("ne"): "north_east",
                 frozenset("nw"): "north_west"}
            shape = m[frozenset(ds)]
        elif ds and ds[0] in "ew":
            shape = "east_west"
        else:
            shape = "north_south"
        d.set(x, y, z, rail(shape))


def ore_heap(d, x, y, z, kinds=("raw_iron_block", "coal_block", "gravel")):
    """Small 2x2 heap of mined material with a slab cap."""
    d.set(x, y, z, kinds[0])
    d.set(x + 1, y, z, kinds[1 % len(kinds)])
    d.set(x, y, z + 1, kinds[2 % len(kinds)])
    d.set(x + 1, y, z + 1, "gravel")
    d.set(x, y + 1, z, slab("cobblestone"))


def racks(d, cells, n, facing="north"):
    for x, y, z in cells[:n]:
        d.rack(x, y, z, facing)


def lattice(d, x1, z1, x2, z2, y1, y2, post, beam, step=4, skip=()):
    """Timber/steel frame around a rectangle: corner posts y1..y2, ring beams every `step` and at y2."""
    posts(d, [(x1, z1), (x2, z1), (x1, z2), (x2, z2)], y1, y2, post)
    for y in list(range(y1 + step, y2, step)) + [y2]:
        for x in range(x1 + 1, x2):
            for z in (z1, z2):
                if (x, z) not in skip:
                    d.set(x, y, z, logb(beam, "x") if "log" in beam or "wood" in beam else beam)
        for z in range(z1 + 1, z2):
            for x in (x1, x2):
                if (x, z) not in skip:
                    d.set(x, y, z, logb(beam, "z") if "log" in beam or "wood" in beam else beam)


def mtop(L):
    """Height of the miner cluster's head-frame platform (ground 1)."""
    return 10 + 3 * (L - 1)


# ================================================================================================ BUILDING KIT
# Pack-styled, decorated buildings: walls with plinth / framing / quoins, windows with sills, shutters and flower
# boxes, floors with ceiling lights, roofs with trim, chimneys; furniture runs along walls; yard decor.
STY = {
    "Hearthwood": dict(plinth="stone_bricks", wall="calcite", post="stripped_dark_oak_log", frame="stripped_dark_oak_log",
                       shutter="dark_oak", doorwood="dark_oak", floor="oak_planks",
                       wood="dark_oak", wood2="oak", roof="deepslate_tile", end="calcite", glass="glass_pane",
                       fence="dark_oak_fence", path="gravel", border="stone_brick_slab", chimney="bricks",
                       rug=("red_carpet", "orange_carpet"), leaves="oak_leaves", log="oak_log", lamp="lantern",
                       flowers=("potted_red_tulip", "potted_oxeye_daisy", "potted_cornflower", "potted_poppy")),
    "Cascadia": dict(plinth="cobblestone", wall="spruce_log", post="stripped_spruce_log", siding="spruce_planks",
                     batten="stripped_spruce_log", shutter="spruce", doorwood="spruce", trim=None, floor="spruce_planks",
                     wood="spruce", wood2="dark_oak", roof="spruce", end="spruce_planks", glass="glass_pane",
                     fence="spruce_fence", path="coarse_dirt", border="cobblestone_slab", chimney="cobblestone",
                     rug=("brown_carpet", "green_carpet"), leaves="spruce_leaves", log="spruce_log", lamp="lantern",
                     flowers=("potted_fern", "potted_blue_orchid", "potted_dandelion", "potted_spruce_sapling")),
    "Neoterra": dict(plinth="polished_andesite", wall="white_concrete", post="light_gray_concrete",
                     band="light_gray_concrete", accent="cyan_terracotta", shutter="birch", doorwood="birch",
                     floor="polished_diorite", wood="birch", wood2="mangrove", roof="smooth_quartz",
                     end="white_concrete", glass="glass_pane", fence="birch_fence", path="smooth_stone",
                     border="polished_andesite_slab", chimney="light_gray_concrete",
                     rug=("cyan_carpet", "light_gray_carpet"), leaves="azalea_leaves", log="birch_log",
                     lamp="sea_lantern",
                     flowers=("potted_bamboo", "potted_azalea_bush", "potted_fern", "potted_white_tulip")),
}
SIDES = {"n": "north", "s": "south", "e": "east", "w": "west"}


def sty(d):
    """The design's palette: the pack's defaults overridden per building type (d.palette)."""
    return dict(STY[d.pack], **getattr(d, "palette", {}))


def leaves(kind):
    return f"{kind}[distance=7,persistent=true,waterlogged=false]"


def wall_block(pack, x, y, z, rel, fh, corner, along, storey, S=None):
    S = S or STY[pack]
    p = x if along == "x" else z
    if pack == "Hearthwood":
        fr = S["frame"]
        if corner:
            return logb(fr, "y")
        if y == 2:
            return S["plinth"]
        if rel == fh - 1:
            return logb(fr, along)
        if S.get("framing", True):
            return logb(fr, "y") if p % 3 == 0 else S["wall"]
        return S["wall"]
    if pack == "Cascadia":
        if corner:
            return logb(S["post"], "y")
        if y == 2:
            return "mossy_cobblestone" if (x * 3 + z) % 5 == 0 and S["plinth"] == "cobblestone" else S["plinth"]
        if storey == 0 and S["wall"].endswith("_log"):
            return logb(S["wall"], along)
        if rel == fh - 1:
            return S["trim"] or logb(S["batten"], along)
        return logb(S["batten"], "y") if p % 2 == 0 else S["siding"]
    # Neoterra
    if corner:
        return S["post"]
    if y == 2:
        return S["plinth"]
    if rel == fh - 1:
        return S["band"]
    return S["wall"]


class R:
    """Result of bld(): the footprint, storey floor levels and roof top."""
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def inner(self):
        return self.x1 + 1, self.z1 + 1, self.x2 - 1, self.z2 - 1


def door_cells(d):
    if not hasattr(d, "_doors"):
        d._doors = set()
    return d._doors


def bld(d, x1, z1, x2, z2, floors=1, fh=4, roof="gable", axis="x", doors=(), win=3, chimney=None,
        floor=None, nowin=(), glass=None, deco=True, overhang=1, roofmat=None, lamps=True, ceiling=True,
        wallfn=None, ribbon=False, pal=None, blind=()):
    """Decorated building shell. doors: (x, z, side[, storey]) with side n/s/e/w = which wall it is in.
    Storey k: air y = 2+k*fh .. fh+k*fh, ceiling/floor slab at 1+(k+1)*fh. Roof eave at top+1."""
    pack = d.pack
    S = dict(sty(d), **(pal or {}))
    top = 1 + floors * fh
    glass = glass or S["glass"]
    wf = wallfn or (lambda x, y, z, rel, corner, along, k: wall_block(pack, x, y, z, rel, fh, corner, along, k, S))
    d.fill(x1, 1, z1, x2, 1, z2, floor or S["floor"])
    for y in range(2, top + 1):
        k = (y - 2) // fh
        rel = (y - 2) % fh
        for z in range(z1, z2 + 1):
            for x in range(x1, x2 + 1):
                edge = x in (x1, x2) or z in (z1, z2)
                if edge:
                    corner = x in (x1, x2) and z in (z1, z2)
                    along = "x" if z in (z1, z2) else "z"
                    d.set(x, y, z, wf(x, y, z, rel, corner, along, k))
                elif rel == fh - 1 and (ceiling or y < top):
                    d.set(x, y, z, floor or S["floor"])
                else:
                    d.set(x, y, z, AIR)
    dl = door_cells(d)
    dpos = []
    for dd in doors:
        x, z, side = dd[:3]
        k = dd[3] if len(dd) > 3 else 0
        dpos.append((x, z, side, k))
    # windows with sills / shutters / boxes
    sides = {"n": [(x, z1) for x in range(x1 + 2, x2 - 1)], "s": [(x, z2) for x in range(x1 + 2, x2 - 1)],
             "w": [(x1, z) for z in range(z1 + 2, z2 - 1)], "e": [(x2, z) for z in range(z1 + 2, z2 - 1)]}
    for k in range(floors):
        yb = 2 + k * fh
        for side, cells in sides.items():
            if side in blind:
                continue
            out = D4[SIDES[side]]
            for i, (x, z) in enumerate(cells):
                p = x if side in "ns" else z
                if (p - (x1 + 2 if side in "ns" else z1 + 2)) % win != (win // 2 if not ribbon else 0) and not ribbon:
                    continue
                if any(abs((x if side in "ns" else z) - (dx if side in "ns" else dz)) <= 1 and ds == side and dk == k
                       for dx, dz, ds, dk in dpos):
                    continue
                if (x, z) in nowin or (x, z, k) in nowin:
                    continue
                if ribbon and pack == "Neoterra" and p % 4 == 0:
                    continue
                ys = range(yb + 1, yb + fh - 1)
                for y in ys:
                    d.set(x, y, z, glass)
                if not deco:
                    continue
                ox, oz = x + out[0], z + out[1]
                ylo, yhi = yb + 1, yb + fh - 2
                if not d.bp.inside(ox, ylo, oz):
                    continue
                if pack == "Hearthwood":
                    d.set(ox, ylo - 1, oz, trap(S["frame"].replace("stripped_", "").replace("_log", ""), SIDES[side], "top", False))
                    d.set(ox, ylo, oz, S["flowers"][(x + z) % 4])
                    if not ribbon:
                        sx, sz = (1, 0) if side in "ns" else (0, 1)
                        for s in (-1, 1):
                            for y in range(ylo, yhi + 1):
                                c = (ox + sx * s, y, oz + sz * s)
                                if d.bp.inside(*c) and d.air(*c):
                                    d.set(*c, trap(S["shutter"], OPP[SIDES[side]], "bottom", True))
                elif pack == "Cascadia":
                    sx, sz = (1, 0) if side in "ns" else (0, 1)
                    for s in (-1, 1):
                        for y in range(ylo, yhi + 1):
                            c = (ox + sx * s, y, oz + sz * s)
                            if d.bp.inside(*c) and d.air(*c):
                                d.set(*c, trap(S["shutter"], OPP[SIDES[side]], "bottom", True))
                    if d.air(x, yhi + 1, z) is False:
                        d.set(x, yhi + 1, z, logb(S["batten"], "x" if side in "ns" else "z"))
                    if k > 0:
                        d.set(ox, ylo - 1, oz, "spruce_slab[type=top,waterlogged=false]")
                else:
                    d.set(ox, yhi + 1, oz, slab("smooth_quartz", "top"))
    for x, z, side, k in dpos:
        y = 2 + k * fh
        d.door(x, y, z, OPP[SIDES[side]], S["doorwood"])
        dl.add((x, y, z))
        out = D4[SIDES[side]]
        dl.add((x + out[0], y, z + out[1]))
        dl.add((x - out[0], y, z - out[1]))
        if deco and pack != "Neoterra" and d.bp.inside(x, y + 2, z):
            d.set(x, y + 2, z, logb(S["post"] if pack == "Cascadia" else S["frame"], "x" if side in "ns" else "z"))
        if deco and d.bp.inside(x + out[0], y + 2, z + out[1]) and k == 0:
            if pack == "Neoterra":
                for s in (-1, 0, 1):
                    sx, sz = (1, 0) if side in "ns" else (0, 1)
                    c = (x + out[0] + sx * s, y + 3, z + out[1] + sz * s)
                    if d.bp.inside(*c) and d.air(*c):
                        d.set(*c, slab("smooth_quartz", "top"))
            else:
                sx, sz = (1, 0) if side in "ns" else (0, 1)
                c = (x + out[0] + sx, y + 2, z + out[1] + sz)
                if d.bp.inside(*c) and d.air(*c) and not d.air(x + sx, y + 2, z + sz):
                    d.set(*c, f"wall_torch[facing={SIDES[side]}]")
    # ceiling lights
    if lamps:
        for k in range(floors):
            yl = fh + k * fh
            for x in range(x1 + 2, x2 - 1, 4):
                for z in range(z1 + 2, z2 - 1, 4):
                    if pack == "Neoterra":
                        if not d.air(x, yl + 1, z) or k == floors - 1:
                            d.set(x, yl + 1, z, "sea_lantern" if k == floors - 1 else "pearlescent_froglight[axis=y]")
                    elif d.air(x, yl, z):
                        d.set(x, yl, z, "lantern[hanging=true,waterlogged=false]")
    # roof
    ridge = top
    rm = roofmat or S["roof"]
    if roof == "gable":
        ridge = d.gable(x1, z1, x2, z2, top + 1, axis, f"{rm}_stairs", f"{rm}_slab", S["end"], overhang=overhang)
        if deco:
            gable_deco(d, x1, z1, x2, z2, top, ridge, axis, S)
    elif roof == "hip":
        ridge = d.hip(x1, z1, x2, z2, top + 1, f"{rm}_stairs", f"{rm}_slab", overhang=overhang)
    elif roof == "flat":
        if pack == "Neoterra":
            d.flat(x1, z1, x2, z2, top + 1, S.get("deck", "smooth_quartz"), S.get("parapet", "white_concrete"),
                   S.get("coping", "smooth_quartz_slab"))
            if S.get("accent"):
                for xx in range(x1, x2 + 1):
                    for zz in (z1, z2):
                        d.set(xx, top, zz, S["accent"])
                for zz in range(z1, z2 + 1):
                    for xx in (x1, x2):
                        d.set(xx, top, zz, S["accent"])
        else:
            d.flat(x1, z1, x2, z2, top + 1, f"{S['wood']}_planks", f"{S['wood']}_planks", f"{S['wood']}_slab")
        ridge = top + 2
    elif roof == "gambrel":
        ridge = gambrel(d, x1, z1, x2, z2, top + 1, rm, f"{S['wood2']}_planks", S["end"])
    if chimney:
        cx, cz = chimney
        for y in range(2, ridge + 3):
            d.set(cx, y, cz, S["chimney"])
        d.set(cx, ridge + 3, cz, slab("brick" if pack == "Hearthwood" else
                                      ("cobblestone" if pack == "Cascadia" else "smooth_quartz")))
    return R(x1=x1, z1=z1, x2=x2, z2=z2, top=top, ridge=ridge, fh=fh, floors=floors,
             ys=[2 + k * fh for k in range(floors)])


def gable_deco(d, x1, z1, x2, z2, top, ridge, axis, S=None):
    """Gable ends: timber king post (Hearthwood) / battens (Cascadia), loft window, bargeboard lantern."""
    pack = d.pack
    if axis == "x":
        ends = [(x1, z) for z in range(z1 + 1, z2)], [(x2, z) for z in range(z1 + 1, z2)]
        mid = (z1 + z2) // 2
        cells = [(x1, mid), (x2, mid)]
    else:
        mid = (x1 + x2) // 2
        cells = [(mid, z1), (mid, z2)]
    for cx, cz in cells:
        for y in range(top + 1, ridge):
            S = S or STY[pack]
            if pack == "Hearthwood" and d.get(cx, y, cz).endswith(S["end"]):
                d.set(cx, y, cz, logb(S["frame"], "y"))
            if pack == "Cascadia" and d.get(cx, y, cz).endswith(S["end"]):
                d.set(cx, y, cz, logb(S["batten"], "y"))
        if ridge - top >= 4:
            for dd in (-1, 1):
                ax, az = (cx, cz + dd) if axis == "x" else (cx + dd, cz)
                if not d.air(ax, top + 2, az) and "stairs" not in d.get(ax, top + 2, az):
                    d.set(ax, top + 2, az, (S or STY[pack])["glass"])


# ---- hand-placed rooms ------------------------------------------------------------------------------------------
# A room frame maps fixed layout coordinates (u along the "back" wall from its left end, v = rows away from the back
# wall) to the building's interior cells. Layouts below put every piece at a fixed (u, v); a piece is left out only
# if its cell is taken by a stair, door way or required block (so a layout never shifts things around).
class Rm:
    def __init__(self, d, r, y, back, wood=None):
        self.d, self.y, self.back = d, y, back
        self.ix1, self.iz1, self.ix2, self.iz2 = r.x1 + 1, r.z1 + 1, r.x2 - 1, r.z2 - 1
        ns = back in "ns"
        self.W = (self.ix2 - self.ix1 + 1) if ns else (self.iz2 - self.iz1 + 1)
        self.D = (self.iz2 - self.iz1 + 1) if ns else (self.ix2 - self.ix1 + 1)
        self.wood = wood or sty(d)["wood"]
        self.f = {"in": OPP[SIDES[back]], "back": SIDES[back],
                  "ur": {"n": "east", "s": "west", "w": "north", "e": "south"}[back]}
        self.f["ul"] = OPP[self.f["ur"]]

    def xz(self, u, v):
        if u < 0:
            u += self.W
        if v < 0:
            v += self.D
        b = self.back
        if b == "n":
            return self.ix1 + u, self.iz1 + v
        if b == "s":
            return self.ix2 - u, self.iz2 - v
        if b == "w":
            return self.ix1 + v, self.iz2 - u
        return self.ix2 - v, self.iz1 + u

    def ok(self, u, v, dy=0):
        if not (-self.W <= u < self.W and -self.D <= v < self.D):
            return False
        x, z = self.xz(u, v)
        y = self.y + dy
        return self.d.air(x, y, z) and (x, y, z) not in door_cells(self.d) and \
            (x, self.y, z) not in door_cells(self.d)

    def put(self, u, v, block, dy=0):
        if not self.ok(u, v, dy):
            return False
        x, z = self.xz(u, v)
        for k, val in self.f.items():
            block = block.replace("{" + k + "}", val)
        self.d.set(x, self.y + dy, z, block.replace("{w}", self.wood))
        return True

    def item(self, u, v, name, facing="in"):
        if self.ok(u, v):
            x, z = self.xz(u, v)
            self.d.item(x, self.y, z, name, self.f.get(facing, facing))
            return True
        return False

    def rack(self, u, v, facing="in"):
        if self.ok(u, v):
            x, z = self.xz(u, v)
            self.d.rack(x, self.y, z, self.f.get(facing, facing))
            return True
        return False

    def chair(self, u, v, back_side):
        if self.ok(u, v):
            x, z = self.xz(u, v)
            self.d.chair(x, self.y, z, self.f.get(back_side, back_side), self.wood, sit=False)

    def bed(self, u, v, color=None):
        """Bed with its head against the back wall at (u, v=0..)."""
        if self.ok(u, v) and self.ok(u, v + 1):
            x, z = self.xz(u, v)
            self.d.bed(x, self.y, z, self.f["back"], color)

    def rug(self, u1, v1, u2, v2, colors):
        for u in range(u1, u2 + 1):
            for v in range(v1, v2 + 1):
                edge = u in (u1, u2) or v in (v1, v2)
                self.put(u, v, colors[0 if edge or len(colors) == 1 else 1])


def need_racks(d):
    return max(0, d.req["racks"] - d.placed["racks"])


SLAB = "{w}_slab[type=top,waterlogged=false]"
POT = "decorated_pot[cracked=false,facing={in},waterlogged=false]"
CANDLE = "candle[candles=3,lit=false,waterlogged=false]"
LANT = "lantern[hanging=false,waterlogged=false]"
BARREL = "barrel[facing=up,open=false]"
CHEST = "chest[facing={in},type=single,waterlogged=false]"
BOOKS = ("chiseled_bookshelf[facing={in},slot_0_occupied=true,slot_1_occupied=false,slot_2_occupied=true,"
         "slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")
LECTERN = "lectern[facing={in},has_book=true,powered=false]"


class P:
    """Furniture pieces for counter(): each is placed at one fixed (u, v) of a room frame."""
    @staticmethod
    def item(name):
        return lambda rm, u, v: rm.item(u, v, name)

    @staticmethod
    def rack():
        return lambda rm, u, v: rm.rack(u, v)

    @staticmethod
    def b(state, top=None):
        def f(rm, u, v):
            if rm.put(u, v, state.replace("{f}", "{in}")) and top:
                rm.put(u, v, top.replace("{f}", "{in}"), 1)
        return f

    @staticmethod
    def shelf(wood, top):
        def f(rm, u, v):
            if rm.put(u, v, wood if "[" in wood else f"{wood}_slab[type=top,waterlogged=false]") and top:
                rm.put(u, v, top, 1)
        return f

    @staticmethod
    def chair(wood):
        return lambda rm, u, v: rm.chair(u, v, "back")

    @staticmethod
    def books():
        return lambda rm, u, v: rm.put(u, v, BOOKS)


def counter(d, r, side, y, u0, props, v=0, wood=None):
    """A run of furniture against one wall: piece i stands at the fixed cell (u0 + i, v) of the room frame."""
    rm = Rm(d, r, y, side, wood)
    for i, pc in enumerate(props):
        pc(rm, u0 + i, v)
    return rm


def rack_bay(d, r, side, y, u0, n=None, v=0):
    """Shelving bay of racks side by side from (u0, v); n defaults to what the level still needs."""
    rm = Rm(d, r, y, side)
    n = need_racks(d) if n is None else n
    for i in range(n):
        rm.rack(u0 + i, v)


def floor_rug(d, r, y, colors=None, inset=2):
    """Rug on a fixed rectangle: the room minus `inset` cells along every wall."""
    rm = Rm(d, r, y, "n")
    rm.rug(inset - 1, inset - 1, rm.W - inset, rm.D - inset, colors or sty(d)["rug"])


def lay_kitchen(rm, dining=True):
    """Counter run on the back wall (range, worktop, sink, worktop, sack) and a dining table in the middle."""
    for u, (b, top) in enumerate([("smoker[facing={in},lit=true]", None), (SLAB, POT),
                                  ("water_cauldron[level=3]", None), (SLAB, CANDLE), (BARREL, "white_wool")]):
        if u < rm.W - 1 and rm.put(u, 0, b) and top:
            rm.put(u, 0, top, 1)
    if dining and rm.D >= 5:
        c = rm.W // 2
        v = min(3, rm.D - 3)
        for u in (c - 1, c):
            if rm.ok(u, v):
                rm.put(u, v, "{w}_fence")
                rm.put(u, v, "{w}_pressure_plate[powered=false]", 1)
                rm.chair(u, v - 1, "back")
                rm.chair(u, v + 1, "in")


def lay_lounge(rm, u0=0):
    """Fireside corner: two armchairs and a low table on a rug, a bookcase on the back wall."""
    rm.put(u0, 0, BOOKS)
    rm.put(u0 + 1, 0, BOOKS)
    rm.put(u0 + 2, 0, SLAB)
    rm.put(u0 + 2, 0, "potted_fern", 1)
    rm.rug(u0, 1, u0 + 2, 3, sty(rm.d)["rug"])
    rm.chair(u0, 2, "in")
    rm.chair(u0 + 2, 2, "in")
    rm.put(u0 + 1, 2, "{w}_slab[type=bottom,waterlogged=false]")


def lay_office(rm):
    """Desk facing the door with a chair behind it, bookcases and a lectern on the back wall, plant by the desk."""
    c = rm.W // 2
    rm.put(0, 0, BOOKS)
    rm.put(1, 0, BOOKS)
    rm.put(-1, 0, LECTERN)
    rm.put(c, 2, SLAB)
    rm.put(c, 2, CANDLE, 1)
    rm.put(c + 1, 2, SLAB)
    rm.put(c + 1, 2, "potted_azalea_bush", 1)
    rm.chair(c, 1, "back")
    rm.put(-1, 2, "potted_bamboo" if rm.d.pack == "Neoterra" else "potted_fern")
    rm.rug(c - 1, 3, c + 1, 4, sty(rm.d)["rug"])


def lay_bunks(rm, n=3, color=None):
    """Beds with their heads on the back wall, a nightstand with a candle between each pair, chests at the feet."""
    u = 0
    for i in range(n):
        if u + 1 > rm.W:
            break
        rm.bed(u, 0, color)
        rm.put(u + 1, 0, SLAB)
        rm.put(u + 1, 0, "candle[candles=1,lit=false,waterlogged=false]", 1)
        rm.put(u, 3, CHEST)
        u += 2


def lay_store(rm, racks=0, rows=(0,), kinds=(BARREL, "{w}_planks", BARREL)):
    """Shelving bays: racks first, then barrels stacked two high, on the given back-wall rows."""
    for v in rows:
        for u in range(0, rm.W - 1):
            if racks > 0:
                if rm.rack(u, v):
                    racks -= 1
                continue
            if rm.put(u, v, kinds[u % len(kinds)]):
                rm.put(u, v, BARREL if u % 2 else "brown_wool", 1)
    return racks


def lay_workshop(rm, bench):
    """Work bench run on the back wall (list of states), tool rack lanterns and a stool at a centre table."""
    for u, b in enumerate(bench):
        rm.put(u, 0, b)
    c = rm.W // 2
    if rm.D >= 5:
        rm.put(c, 2, SLAB)
        rm.put(c, 2, LANT, 1)
        rm.chair(c, 3, "in")


def lay_lab(rm):
    rm.put(0, 0, SLAB)
    rm.put(0, 0, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]", 1)
    rm.put(1, 0, "water_cauldron[level=3]")
    rm.put(2, 0, SLAB)
    rm.put(2, 0, "potted_cactus", 1)
    rm.put(3, 0, BOOKS)
    rm.put(-1, 0, LECTERN)
    rm.chair(1, 2, "back")


def lay_shop(rm, goods=("melon", "pumpkin", BARREL)):
    """Shop counter across the room with the till, goods on shelves behind it."""
    for u in range(0, rm.W - 1):
        rm.put(u, 0, SLAB)
        rm.put(u, 0, goods[u % len(goods)], 1)
    for u in range(1, rm.W - 1):
        rm.put(u, 2, SLAB if u != rm.W - 2 else AIR)
    rm.put(1, 2, CANDLE, 1)


# ---- material economy on levels 1-3 ------------------------------------------------------------------------------
# Early levels are built from common materials; premium blocks (quartz, blackstone, prismarine, sea lanterns, ...)
# arrive with the L4-5 upgrades. Only the hut's own construction is converted - the functional cluster keeps its
# blocks.
ECONOMY = [  # (premium prefix, common replacement, keep block-state properties)
    ("smooth_quartz_slab", "smooth_stone_slab", True), ("smooth_quartz_stairs", "polished_diorite_stairs", True),
    ("smooth_quartz", "smooth_stone", False), ("quartz_block", "calcite", False), ("quartz_pillar", "calcite", False),
    ("quartz_bricks", "calcite", False),
    ("polished_blackstone_brick_slab", "deepslate_brick_slab", True),
    ("polished_blackstone_brick_stairs", "deepslate_brick_stairs", True),
    ("polished_blackstone_brick_wall", "deepslate_brick_wall", True),
    ("polished_blackstone_bricks", "deepslate_bricks", False),
    ("polished_blackstone_slab", "polished_deepslate_slab", True),
    ("polished_blackstone_stairs", "polished_deepslate_stairs", True),
    ("polished_blackstone", "polished_deepslate", False), ("blackstone", "cobbled_deepslate", False),
    ("sea_lantern", "glowstone", False), ("pearlescent_froglight", "glowstone", False),
    ("iron_block", "polished_andesite", False),
]
ECONOMY_ROOF = {"Hearthwood": "deepslate_tile", "Cascadia": "warped", "Neoterra": "polished_deepslate"}


def economize(d):
    if d.level > 3:
        return
    from blueprint import parse_state, format_state
    rules = list(ECONOMY) + [("dark_prismarine_stairs", ECONOMY_ROOF[d.pack] + "_stairs", True),
                             ("dark_prismarine_slab", ECONOMY_ROOF[d.pack] + "_slab", True),
                             ("dark_prismarine", "deepslate_tiles" if d.pack != "Cascadia" else "warped_planks", False)]
    bp = d.bp
    for y in range(bp.sy):
        for z in range(bp.sz):
            row = bp.grid[y][z]
            for x in range(bp.sx):
                st = row[x]
                if not st.startswith("minecraft:"):
                    continue
                n = st.split("[")[0][10:]
                for pre, rep, keep in rules:
                    if n == pre:
                        name, props = parse_state(st)
                        row[x] = format_state("minecraft:" + rep, props if keep else {})
                        break


def paste_cluster(d, x0, z0):
    economize(d)
    d.cluster(x0, z0)


def stairs_up(d, x, z, dirn, y0, fh=4, wood=None, rail=True):
    """Straight flight from floor y0 rising fh to the next floor, heading `dirn`; clears the ceiling above."""
    wood = wood or sty(d)["wood"]
    st = f"{wood}_stairs" if d.pack != "Neoterra" else "polished_diorite_stairs"
    dl = door_cells(d)
    dx0, dz0 = D4[dirn]
    dl.add((x - dx0, y0, z - dz0))
    dl.add((x + dx0 * fh, y0 + fh, z + dz0 * fh))
    for i in range(fh):
        for k in (1, 2, 3):
            dl.add((x + dx0 * i, y0 + i + k, z + dz0 * i))
    full = f"{wood}_planks" if d.pack != "Neoterra" else "polished_diorite"
    dx, dz = D4[dirn]
    for i in range(fh):
        cx, cz = x + dx * i, z + dz * i
        d.set(cx, y0 + i, cz, stair(st, dirn))
        for y in range(y0, y0 + i):
            d.set(cx, y, cz, full)
        for y in range(y0 + i + 1, y0 + fh + 2):
            if y != y0 + fh + 1 or i > 0:
                d.set(cx, y, cz, AIR)
    if rail:
        sx, sz = (1, 0) if dz else (0, 1)
        for i in range(1, fh):
            for s in (-1, 1):
                c = (x + dx * i + sx * s, y0 + fh, z + dz * i + sz * s)
                if d.bp.inside(*c) and d.air(*c) and not d.air(c[0], y0 + fh - 1, c[2]):
                    d.set(*c, sty(d)["fence"] if d.pack != "Neoterra" else "glass_pane")
                    break


def porch(d, x1, x2, zw, depth=3, side="n", gaps=(), chairs=True, ylevel=6):
    """Covered porch along the front wall z = zw (side n: out toward -z, s: toward +z): deck, posts, shed roof,
    railing with gaps at the door x positions, rocking chairs and lanterns."""
    S = sty(d)
    w = S["wood"] if d.pack != "Neoterra" else "birch"
    sg = -1 if side == "n" else 1
    zo = zw + sg * depth                                            # outer row
    zs = sorted((zw + sg, zo))
    d.fill(x1, 1, zs[0], x2, 1, zs[1], f"{w}_planks")
    for x in sorted({x1, x2} | set(range(x1, x2 + 1, 4))):
        if x in gaps:
            x += 1 if x < x2 else -1
        for y in range(2, ylevel):
            d.set(x, y, zo, logb(f"{w}_log" if d.pack != "Neoterra" else "stripped_birch_log", "y"))
    for x in range(x1 - 1, x2 + 2):
        d.set(x, ylevel, zo + sg, stair(w, "south" if side == "n" else "north"))
        for z in range(zs[0], zs[1] + 1):
            d.set(x, ylevel, z, slab(w))
    for x in range(x1 + 1, x2):
        if d.air(x, 2, zo) and all(abs(x - g) > 0 for g in gaps):
            d.set(x, 2, zo, S["fence"])
    if chairs:
        for x in (x1 + 1, x2 - 1):
            if d.air(x, 2, zw + sg) and all(abs(x - g) > 1 for g in gaps):
                d.chair(x, 2, zw + sg, "north" if side == "s" else "south", w, sit=False)
    for x in range(x1 + 2, x2 - 1, 4):
        d.set(x, ylevel - 1, zw + sg * (1 + depth // 2) if depth > 1 else zw + sg,
              "lantern[hanging=true,waterlogged=false]")


def glasswall(pack, frame="white_concrete", glass="glass"):
    """Wall function for greenhouse / curtain-wall shells."""
    def f(x, y, z, rel, corner, along, k):
        if corner or y == 2:
            return frame
        if rel == 3:
            return frame
        p = x if along == "x" else z
        return frame if p % 4 == 0 else glass
    return f


# ---- yard decor ---------------------------------------------------------------------------------------------
def tree(d, x, z, h=4, kind=None, log=None, r=2):
    S = sty(d)
    kind = kind or S["leaves"]
    log = log or S["log"]
    for y in range(2, 2 + h):
        d.set(x, y, z, logb(log, "y"))
    for y in range(h, h + 3):
        rr = r if y < h + 2 else 1
        for dx in range(-rr, rr + 1):
            for dz in range(-rr, rr + 1):
                if abs(dx) == rr and abs(dz) == rr and rr > 1:
                    continue
                c = (x + dx, y, z + dz)
                if d.bp.inside(*c) and d.air(*c):
                    d.set(*c, leaves(kind))
    d.set(x, h + 3, z, leaves(kind))


def bush(d, x, z, kind=None):
    d.set(x, 2, z, leaves(kind or sty(d)["leaves"]))


def lamp_post(d, x, z, h=3):
    S = sty(d)
    if d.pack == "Neoterra":
        for y in range(2, 2 + h):
            d.set(x, y, z, "light_gray_concrete" if y == 2 else "iron_bars")
        d.set(x, 2 + h, z, "sea_lantern")
        d.set(x, 3 + h, z, slab("smooth_quartz"))
    else:
        for y in range(2, 2 + h):
            d.set(x, y, z, S["fence"])
        d.set(x, 2 + h, z, "lantern[hanging=false,waterlogged=false]")


def bench(d, x, z, back, n=2):
    S = sty(d)
    a = (1, 0) if back in ("north", "south") else (0, 1)
    for i in range(n):
        d.chair(x + a[0] * i, 2, z + a[1] * i, back, S["wood"], sit=False)
    for s, c in ((-1, (x - a[0], z - a[1])), (1, (x + a[0] * n, z + a[1] * n))):
        side = [k for k, v in D4.items() if v == (a[0] * s, a[1] * s)][0]
        if d.bp.inside(c[0], 2, c[1]) and d.air(c[0], 2, c[1]):
            d.set(c[0], 2, c[1], trap(S["wood"], side, "bottom", True))


def flowerbed(d, x1, z1, x2, z2, flowers=("poppy", "dandelion", "azure_bluet", "oxeye_daisy", "cornflower",
                                            "allium")):
    S = sty(d)
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            edge = x in (x1, x2) or z in (z1, z2)
            d.set(x, 1, z, "grass_block[snowy=false]")
            if edge and d.pack != "Cascadia":
                d.set(x, 2, z, f"{S['border']}[type=bottom,waterlogged=false]")
            else:
                d.set(x, 2, z, flowers[(x * 3 + z) % len(flowers)])


def path(d, cells, border=True):
    S = sty(d)
    for x, z in cells:
        d.set(x, 1, z, S["path"] if d.pack != "Hearthwood" else "gravel")


def cart(d, x, z, axis="x", load="hay_block[axis=y]"):
    """Farm cart: plank bed on two wheels (trapdoors), shafts (fences) and a load."""
    S = sty(d)
    w = S["wood"] if d.pack != "Neoterra" else "spruce"
    a = (1, 0) if axis == "x" else (0, 1)
    b = (0, 1) if axis == "x" else (1, 0)
    for i in range(2):
        cx, cz = x + a[0] * i, z + a[1] * i
        d.set(cx, 2, cz, f"{w}_slab[type=top,waterlogged=false]")
        d.set(cx, 3, cz, load if i == 0 else "pumpkin")
    for s in (-1, 1):
        cx, cz = x + b[0] * s, z + b[1] * s
        side = [k for k, v in D4.items() if v == (b[0] * s, b[1] * s)][0]
        if d.air(cx, 2, cz):
            d.set(cx, 2, cz, trap(w, side, "bottom", True))
    fx, fz = x - a[0], z - a[1]
    if d.air(fx, 2, fz):
        d.set(fx, 2, fz, f"{w}_fence")


def woodpile(d, x, z, n=3, axis="x"):
    a = (1, 0) if axis == "x" else (0, 1)
    for i in range(n):
        d.set(x + a[0] * i, 2, z + a[1] * i, logb("oak_log" if d.pack != "Cascadia" else "spruce_log",
                                                     "z" if axis == "x" else "x"))
        if i < n - 1:
            d.set(x + a[0] * i, 3, z + a[1] * i, logb("oak_log" if d.pack != "Cascadia" else "spruce_log",
                                                         "z" if axis == "x" else "x"))


def fence_line(d, pts, gate=None):
    S = sty(d)
    for x, z in pts:
        d.set(x, 2, z, S["fence"])
    if gate:
        x, z, f = gate
        d.set(x, 2, z, f"{S['wood']}_fence_gate[facing={f},in_wall=false,open=false,powered=false]")


def hay_rick(d, x, z):
    for dx in range(2):
        for dz in range(2):
            d.set(x + dx, 2, z + dz, "hay_block[axis=y]")
    d.set(x, 3, z, "hay_block[axis=x]")
    d.set(x + 1, 3, z + 1, "hay_block[axis=z]")
    d.set(x, 3, z + 1, "hay_block[axis=y]")


def well(d, x, z):
    S = sty(d)
    stone = "cobblestone" if d.pack != "Neoterra" else "polished_andesite"
    for dx in range(3):
        for dz in range(3):
            d.set(x + dx, 2, z + dz, stone if (dx, dz) != (1, 1) else "water")
    d.set(x + 1, 1, z + 1, "water")
    d.set(x + 1, 0, z + 1, "water")
    for dx in (0, 2):
        d.set(x + dx, 3, z + 1, S["fence"])
        d.set(x + dx, 4, z + 1, S["fence"])
    w = S["wood"] if d.pack != "Neoterra" else "spruce"
    d.set(x, 5, z + 1, stair(w, "east"))
    d.set(x + 1, 5, z + 1, slab(w))
    d.set(x + 2, 5, z + 1, stair(w, "west"))
    for dz in (0, 2):
        for dx in range(3):
            d.set(x + dx, 5, z + dz, stair(w, "south" if dz == 0 else "north"))
    d.set(x + 1, 4, z + 1, CHAIN)


# ================================================================================================== MINER
def mine_items(d, r, side, y=2, skip=1, hopper=True):
    """Furnace (with the ore hopper on top from L2), crafting table, first racks."""
    rm = counter(d, r, side, y, skip, [P.item("furnace"), P.item("crafting_table")])
    if hopper and "minecraft:hopper" in d.req["items"]:
        x, z = rm.xz(skip, 0)
        if d.get(x, y, z).startswith("minecraft:furnace") and d.air(x, y + 1, z):
            d.item(x, y + 1, z, "hopper")


def headframe(d, cx, cz, L, post, beam, deck, rail_):
    """Frame around the shaft cluster (4x3 at cx, cz): corner posts to the sheave deck, ring beams, braces."""
    yt = mtop(L)
    lattice(d, cx - 1, cz - 1, cx + 4, cz + 3, 2, yt, post, beam, step=3)
    for y in range(5, yt, 3):
        for x, z, f in ((cx - 1, cz, "south"), (cx - 1, cz + 2, "north"), (cx + 4, cz, "south"), (cx + 4, cz + 2, "north")):
            d.set(x, y - 1, z, stair(beam.replace("stripped_", "").replace("_log", "") if "log" in beam else "stone_brick",
                                     f, "top"))
    for z in range(cz - 1, cz + 4):
        for x in range(cx - 1, cx + 5):
            if x in (cx - 1, cx + 4) or z in (cz - 1, cz + 3):
                d.set(x, yt, z, deck)
                d.set(x, yt + 1, z, rail_)
    return yt


def miner_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (46, 30, 36), gy=1)
    P.d = d
    d.palette = dict(wall="cobblestone", end="cobblestone", framing=False, frame="stripped_spruce_log",
                     roof="deepslate_tile", shutter="mangrove", doorwood="spruce", plinth="stone_bricks", chimney="bricks")
    cx, cz = 20, 12                                                   # shaft cluster 20..23 x 12..14
    yt = headframe(d, cx, cz, L, "dark_oak_log[axis=y]", "stripped_dark_oak_log", "dark_oak_planks", "dark_oak_fence")
    # ---- count house: the mine captain's office (hut) ----
    ch = bld(d, 8, 3, 15, 9, floors=1, axis="x", doors=[(11, 3, "n"), (15, 6, "e")], chimney=(8, 6))
    d.hut(9, 2, 4)
    d.hearth(9, 2, 6, "east", 5, "bricks", "campfire")
    mine_items(d, ch, "s", skip=1)
    counter(d, ch, "n", 2, 3, [P.rack()] * min(2, need_racks(d)) + [P.books()])
    d.set(12, 2, 6, "spruce_slab[type=top,waterlogged=false]")           # assay / pay table
    d.set(12, 3, 6, "candle[candles=3,lit=false,waterlogged=false]")
    d.chair(13, 2, 6, "east", "spruce", sit=False)
    floor_rug(d, ch, 2, inset=3)
    d.sign(13, 4, 2, "north", ["WHEAL", "HEARTH", "Count House"], "spruce")
    lamp_post(d, 16, 2)
    track(d, [(21, z) for z in range(11, 6, -1)] + [(x, 7) for x in range(22, 28)], 2)
    ore_heap(d, 28, 2, 6)
    # ---- L2: Cornish engine house with the tall stack ----
    if L >= 2:
        eh = bld(d, 10, 11, 18, 17, floors=2, fh=5, axis="x", doors=[(14, 17, "s")], chimney=None, win=3,
                 pal=dict(wall="stone_bricks", end="stone_bricks", roof="deepslate_tile", plinth="cobblestone",
                          frame="stripped_dark_oak_log", shutter="dark_oak"))
        for y in range(1, 22):                                        # stack built into the west gable
            for x in (8, 9):
                for z in (13, 14, 15):
                    if (x, z) != (8, 14) or y < 3:
                        d.set(x, y, z, "bricks" if y > 17 or y < 3 else ("cobblestone" if (x + y + z) % 4 == 0 else "stone_bricks"))
        d.set(8, 22, 14, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        d.fill(11, 7, 14, 12, 9, 15, "polished_deepslate")                # beam engine cylinder
        d.set(11, 10, 14, "iron_block")
        for x in range(11, 18):
            d.set(x, 11, 14, "dark_oak_log[axis=x]")                      # rocking beam ("bob") to the shaft
        for y in range(7, 11):
            d.set(17, y, 14, CHAIN)
        stairs_up(d, 15, 12, "south", 2, fh=5, rail=False)
        counter(d, eh, "n", 2, 1, [P.b("blast_furnace[facing={f},lit=true]"), P.b("water_cauldron[level=3]"), P.b("coal_block", "coal_block")])
        counter(d, eh, "s", 7, 1, [P.b("lever[face=floor,facing=north,powered=false]"), P.chair("dark_oak"),
                            P.shelf("dark_oak", "lantern[hanging=false,waterlogged=false]")])
        rack_bay(d, eh, "w", 2, 0)
    # ---- L3: boiler house and ore dressing floor ----
    if L >= 3:
        bh = bld(d, 10, 19, 18, 24, floors=1, axis="x", doors=[(14, 19, "n")], chimney=(18, 22),
                 pal=dict(wall="bricks", end="bricks", roof="spruce", plinth="stone_bricks", frame="stripped_spruce_log"))
        for x in (12, 15):
            d.set(x, 2, 22, "blast_furnace[facing=north,lit=true]")
            d.set(x + 1, 2, 22, "water_cauldron[level=3]")
            d.set(x, 3, 22, "polished_deepslate")
        counter(d, bh, "s", 2, 0, [P.b("coal_block")] * 4)
        # dressing floor: open shed with stone tables and buddles
        for x in range(26, 37, 3):
            for z in (12, 18):
                posts(d, [(x, z)], 2, 5, "dark_oak_log[axis=y]")
        d.gable(26, 12, 36, 18, 6, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "cobblestone", overhang=1)
        for x in range(27, 36):
            if x % 3:
                d.set(x, 2, 14, "smooth_stone_slab[type=top,waterlogged=false]")
                d.set(x, 2, 16, "cauldron" if x % 2 else "smooth_stone_slab[type=top,waterlogged=false]")
        for x in range(27, 36, 2):
            d.set(x, 3, 14, ("raw_iron_block", "raw_copper_block", "gravel", "coal_block", "raw_gold_block")[x % 5])
        track(d, [(x, 15) for x in range(25, 36)], 2)
        rack_bay(d, bh, "n", 2, 1)
        # ore bins: timber hoppers on a stone platform beside the shaft
        for i, x in enumerate((26, 29, 32)):
            d.fill(x, 2, 21, x + 1, 2, 22, "cobblestone")
            walls(d, x, 21, x + 1, 22, 3, 4, "dark_oak_planks")
            d.set(x, 5, 21, ("raw_iron_block", "raw_copper_block", "coal_block")[i])
            d.set(x + 1, 5, 22, "gravel")
            d.set(x, 5, 22, "dark_oak_slab[type=bottom,waterlogged=false]")
        for x in range(25, 35):
            d.set(x, 2, 24, "dark_oak_fence")
        lamp_post(d, 25, 20)
        lamp_post(d, 35, 20)
        cart(d, 37, 15, "x", "raw_iron_block")
        bench(d, 16, 9, "east", 2)
        woodpile(d, 19, 25, 4)
        lamp_post(d, 6, 18)
    # ---- L4: miners' dry (changing house) and powder magazine ----
    if L >= 4:
        dr = bld(d, 26, 2, 37, 9, floors=2, axis="x", doors=[(31, 9, "s")], chimney=(37, 5),
                 pal=dict(wall="white_terracotta", end="white_terracotta", framing=True, roof="brick",
                          frame="stripped_dark_oak_log", shutter="mangrove", plinth="cobblestone"))
        d.hearth(36, 2, 5, "west", 5, "bricks", "campfire")
        for x in range(27, 35, 2):
            d.chair(x, 2, 7, "south", "spruce", sit=False)
            d.set(x, 3, 3, "spruce_trapdoor[facing=south,half=bottom,open=true,powered=false,waterlogged=false]")
            d.set(x, 2, 3, "barrel[facing=south,open=false]")
        stairs_up(d, 27, 5, "east", 2, rail=False)
        for x in (28, 31, 34):
            d.bed(x, 6, 3, "north")
        counter(d, dr, "s", 6, 1, [P.b("chest[facing={f},type=single,waterlogged=false]")] * 3)
        floor_rug(d, dr, 6, inset=2)
        pm = bld(d, 40, 27, 44, 31, floors=1, roof="hip", doors=[(42, 27, "n")], win=99,
                 pal=dict(wall="stone_bricks", plinth="stone_bricks", roof="deepslate_tile", framing=False,
                          frame="stripped_spruce_log"))
        d.set(41, 2, 30, "tnt[unstable=false]")
        d.set(43, 2, 30, "barrel[facing=up,open=false]")
        for x in range(38, 46):
            if x not in (41, 42, 43):
                d.set(x, 2, 25, "stone_brick_wall")
    # ---- L5: smithy, workers' cottages, spoil heap ----
    if L >= 5:
        sm = bld(d, 2, 20, 7, 30, floors=1, axis="z", doors=[(7, 25, "e")], chimney=(2, 23),
                 pal=dict(wall="mud_bricks", end="mud_bricks", roof="mud_brick", plinth="cobblestone",
                          frame="stripped_spruce_log", shutter="spruce"))
        d.hearth(3, 2, 23, "east", 5, "bricks", "campfire")
        counter(d, sm, "w", 2, 3, [P.b("anvil[facing=north]"), P.b("grindstone[face=floor,facing={f}]"),
                            P.b("water_cauldron[level=3]"), P.b("smithing_table")])
        counter(d, sm, "e", 2, 0, [P.b("barrel[facing=up,open=false]", "chain[axis=y,waterlogged=false]")] * 2)
        for i, x0 in enumerate((10, 17, 24)):
            cot = bld(d, x0, 28, x0 + 5, 34, floors=2, axis="z", doors=[(x0 + 2, 28, "n")], chimney=(x0 + 5, 31),
                      pal=dict(wall=("white_terracotta", "yellow_terracotta", "pink_terracotta")[i],
                               end=("white_terracotta", "yellow_terracotta", "pink_terracotta")[i], framing=False,
                               roof=("deepslate_tile", "brick", "mud_brick")[i], shutter=("mangrove", "warped", "dark_oak")[i],
                               plinth="cobblestone"))
            d.hearth(x0 + 4, 2, 31, "west", 5, "bricks", "campfire")
            d.dining(x0 + 2, 2, 31, 2, "z", "spruce", chairs=("w",), sit=False)
            flowerbed(d, x0, 26, x0 + 5, 26)
        for x in range(36, 45):                                       # spoil heap
            for z in range(12, 23):
                h = 3 - (abs(x - 40) + abs(z - 17)) // 3
                for y in range(2, 2 + max(0, h)):
                    d.set(x, y, z, "gravel" if (x + y + z) % 3 else "cobblestone")
        track(d, [(x, 11) for x in range(24, 36)], 2)
    paste_cluster(d, cx, cz)
    return d


def miner_cascadia(rel, L):
    d = Design("Cascadia", rel, (48, 30, 38), gy=1, paving="coarse_dirt")
    P.d = d
    d.palette = dict(wall="spruce_log", siding="spruce_planks", batten="stripped_spruce_log", end="spruce_planks",
                     roof="spruce", shutter="dark_oak", doorwood="dark_oak", plinth="tuff", trim="stripped_dark_oak_log")
    cx, cz = 6, 16                                                    # shaft cluster 6..9 x 16..18
    yt = headframe(d, cx, cz, L, "spruce_log[axis=y]", "stripped_spruce_log", "spruce_planks", "spruce_fence")
    # ---- hoist house (hut) ----
    hh = bld(d, 12, 13, 20, 21, floors=1, axis="z", doors=[(12, 17, "w"), (16, 13, "n")], chimney=(20, 17))
    d.hut(13, 2, 14)
    d.hearth(19, 2, 17, "west", 5, "cobblestone", "campfire")
    mine_items(d, hh, "s", skip=1)
    for z in range(15, 19):                                           # winding drum
        d.set(14, 3, z, "stripped_spruce_log[axis=z]")
    for z in (14, 19):
        if d.air(14, 2, z):
            d.set(14, 2, z, "spruce_fence")
    counter(d, hh, "e", 2, 0, [P.rack()] * min(2, need_racks(d)))
    porch(d, 12, 20, 13, 3, "n", gaps=(16,))
    d.sign(18, 4, 12, "north", ["TIMBERLINE", "MINE", "No. 1"], "spruce")
    track(d, [(cx + 2, z) for z in range(cz - 2, cz - 9, -1)], 2)
    lamp_post(d, 11, 12)
    # back legs raking from the frame onto the hoist house roof
    for k in range(1, 12):
        y = yt - 2 * k
        if y < 2:
            break
        x = cx + 4 + k
        stop = False
        for z in (cz - 1, cz + 3):
            for yy in (y + 1, y):
                if d.air(x, yy, z) or "stairs" in d.get(x, yy, z) or "slab" in d.get(x, yy, z):
                    d.set(x, yy, z, logb("spruce_log", "x"))
                else:
                    stop = True
        if stop:
            break
    # ---- L2: tipple (ore bin on stilts) and assay shed ----
    if L >= 2:
        for x, z in ((6, 3), (10, 3), (6, 7), (10, 7)):
            posts(d, [(x, z)], 2, 9, "spruce_log[axis=y]")
        d.fill(6, 6, 3, 10, 6, 7, "spruce_planks")
        walls(d, 6, 3, 10, 7, 7, 8, "spruce_planks")
        d.fill(7, 7, 4, 9, 7, 6, "raw_iron_block")
        d.set(8, 8, 5, "coal_block")
        d.item(8, 5, 5, "hopper")
        d.gable(6, 3, 10, 7, 9, "z", "spruce_stairs", "spruce_slab", "spruce_planks", overhang=1)
        ladder(d, 5, 5, 2, 7, "west")
        d.set(6, 7, 5, AIR)
        d.set(6, 8, 5, AIR)
        as_ = bld(d, 14, 2, 20, 8, floors=1, axis="x", doors=[(17, 8, "s")],
                  pal=dict(wall="birch_planks", siding="birch_planks", batten="stripped_spruce_log", end="birch_planks",
                           roof="dark_prismarine", shutter="spruce"))
        counter(d, as_, "n", 2, 1, [P.b("brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]"), P.b("blast_furnace[facing={f},lit=true]"),
                             P.shelf("spruce", "lantern[hanging=false,waterlogged=false]"), P.books()])
        rack_bay(d, as_, "w", 2, 0)
        d.sign(17, 4, 9, "south", ["ASSAY", "OFFICE"], "spruce")
    # ---- L3: bunkhouse ----
    if L >= 3:
        bk = bld(d, 24, 2, 35, 9, floors=2, axis="x", doors=[(29, 9, "s")], chimney=(35, 5),
                 pal=dict(wall="dark_oak_log", siding="dark_oak_planks", batten="stripped_dark_oak_log",
                          end="dark_oak_planks", roof="mangrove", shutter="spruce", plinth="cobblestone"))
        d.hearth(34, 2, 5, "west", 5, "cobblestone", "campfire")
        d.dining(27, 2, 5, 4, "x", "spruce", chairs=("n", "s"), sit=False)
        stairs_up(d, 25, 8, "north", 2, rail=False)
        for x in (27, 29, 31, 33):
            d.bed(x, 6, 3, "north")
            d.bed(x, 6, 8, "south")
        floor_rug(d, bk, 6, inset=3)
        porch(d, 24, 35, 9, 2, "s", gaps=(29,))
        rack_bay(d, hh, "e", 2, 0)
    # ---- L4: stamp mill stepping down the slope ----
    if L >= 4:
        mm = bld(d, 24, 16, 36, 27, floors=2, fh=6, axis="x", doors=[(24, 21, "w")], chimney=(36, 21),
                 pal=dict(wall="stripped_spruce_log", siding="spruce_planks", batten="stripped_dark_oak_log",
                          end="spruce_planks", roof="deepslate_tile", shutter="dark_oak", plinth="andesite"))
        for x in range(27, 34, 2):                                    # stamp battery
            for y in range(2, 7):
                d.set(x, y, 18, "stripped_spruce_log[axis=y]" if y < 6 else "iron_block")
            d.set(x, 2, 19, "anvil[facing=north]")
        for x in range(26, 35):
            d.set(x, 7, 18, "spruce_log[axis=x]")
        for z in range(22, 27, 2):
            d.set(26, 2, z, "water_cauldron[level=3]")
            d.set(27, 2, z, "smooth_stone_slab[type=top,waterlogged=false]")
        ladder(d, 35, 26, 2, 7, "west")
        d.set(35, 7, 26, "ladder[facing=west,waterlogged=false]")
        counter(d, mm, "n", 8, 4, [P.b("barrel[facing=up,open=false]")] * 4)
        rack_bay(d, mm, "s", 2, 3)
        track(d, [(x, 23) for x in range(11, 24)], 2)
    # ---- L5: blacksmith, lamp house, rock dump ----
    if L >= 5:
        bs = bld(d, 2, 24, 9, 32, floors=1, axis="z", doors=[(9, 28, "e")], chimney=(2, 28),
                 pal=dict(wall="cobblestone", siding="cobblestone", batten="spruce_log", end="spruce_planks",
                          roof="spruce", plinth="cobblestone", shutter="spruce"))
        d.hearth(3, 2, 28, "east", 5, "cobblestone", "campfire")
        counter(d, bs, "e", 2, 6, [P.b("anvil[facing=north]"), P.b("grindstone[face=floor,facing={f}]"), P.b("water_cauldron[level=3]")])
        counter(d, bs, "n", 2, 0, [P.b("smithing_table"), P.b("barrel[facing=up,open=false]")])
        lh = bld(d, 39, 2, 45, 9, floors=1, axis="z", doors=[(42, 9, "s")],
                 pal=dict(wall="mangrove_planks", siding="mangrove_planks", batten="stripped_spruce_log",
                          end="mangrove_planks", roof="cobbled_deepslate", shutter="birch"))
        for z in range(3, 9):
            d.set(44, 2, z, "spruce_slab[type=top,waterlogged=false]")
            d.set(44, 3, z, "lantern[hanging=false,waterlogged=false]")
        for x in range(39, 47):
            for z in range(14, 30):
                h = 4 - (abs(x - 43) + abs(z - 22)) // 2
                for y in range(2, 2 + max(0, h)):
                    d.set(x, y, z, "gravel" if (x + y * 2 + z) % 3 else ("tuff" if x % 2 else "cobblestone"))
        for x, z in ((14, 34), (20, 34), (28, 33), (46, 35), (2, 36), (8, 36)):
            tree(d, x, z, 6, "spruce_leaves", "spruce_log", 2)
        # cookhouse & mess with a covered dining porch
        ck = bld(d, 12, 26, 22, 33, floors=2, axis="x", doors=[(17, 26, "n")], chimney=(22, 29),
                 pal=dict(wall="spruce_log", siding="birch_planks", batten="stripped_spruce_log", end="birch_planks",
                          roof="dark_prismarine", shutter="mangrove", plinth="cobblestone"))
        d.hearth(21, 2, 29, "west", 5, "cobblestone", "campfire")
        d.dining(14, 2, 29, 5, "x", "spruce", chairs=("n", "s"), sit=False)
        counter(d, ck, "s", 2, 1, [P.b("smoker[facing={f},lit=true]"), P.b("water_cauldron[level=3]"),
                            P.shelf("spruce", "cake[bites=0]"), P.b("barrel[facing=up,open=false]", "brown_wool")])
        stairs_up(d, 13, 32, "east", 2, rail=False)
        for x in (14, 16, 18, 20):
            d.bed(x, 6, 27, "north")
        counter(d, ck, "s", 6, 5, [P.b("chest[facing={f},type=single,waterlogged=false]")] * 3)
        floor_rug(d, ck, 6, inset=2)
        porch(d, 12, 22, 26, 2, "n", gaps=(17,))
    paste_cluster(d, cx, cz)
    return d


def miner_neoterra(rel, L):
    d = Design("Neoterra", rel, (46, 30, 36), gy=1, paving="smooth_stone")
    P.d = d
    d.palette = dict(wall="gray_concrete", post="polished_deepslate", band="yellow_concrete", accent="yellow_concrete",
                     plinth="polished_blackstone", doorwood="iron")
    cx, cz = 6, 8                                                     # shaft cluster 6..9 x 8..10
    yt = mtop(L)
    for y in range(2, yt):                                            # enclosed winding tower
        for x in range(cx - 1, cx + 5):
            for z in range(cz - 1, cz + 4):
                if x in (cx - 1, cx + 4) or z in (cz - 1, cz + 3):
                    corner = x in (cx - 1, cx + 4) and z in (cz - 1, cz + 3)
                    d.set(x, y, z, "polished_deepslate" if corner else
                          ("gray_stained_glass_pane" if (x in (cx + 1, cx + 2) or z == cz + 1) and 3 <= y < yt - 1 else "light_gray_concrete"))
    for y in range(4, yt, 4):
        d.set(cx + 4, y, cz, "sea_lantern")
        d.set(cx + 4, y, cz + 2, "sea_lantern")
    for z in range(cz - 1, cz + 4):
        for x in range(cx - 1, cx + 5):
            if x in (cx - 1, cx + 4) or z in (cz - 1, cz + 3):
                d.set(x, yt, z, "smooth_quartz")
                d.set(x, yt + 1, z, "iron_bars")
    d.fill(cx - 1, yt - 1, cz - 1, cx + 4, yt - 1, cz - 1, "yellow_concrete")
    d.fill(cx - 1, yt - 1, cz + 3, cx + 4, yt - 1, cz + 3, "yellow_concrete")
    d.sign(cx + 1, yt - 2, cz - 2, "north", ["SHAFT", "01"], "birch", glow=True, color="yellow")
    d.door(cx + 4, 2, cz + 1, "west", "iron")
    door_cells(d).update({(cx + 5, 2, cz + 1)})
    # ---- mining station (hut) ----
    fl = 1 if L < 2 else 2
    st_ = bld(d, 11, 5, 19, 13, floors=fl, roof="flat", doors=[(11, 9, "w"), (15, 5, "n")], ribbon=True)
    if fl == 2:
        stairs_up(d, 18, 7, "south", 2, rail=False)
    d.hut(12, 2, 6)
    mine_items(d, st_, "s", skip=1)
    counter(d, st_, "e", 2, 3, [P.rack()] * min(2, need_racks(d)))
    for z in (6, 7):                                                  # lamp room lockers
        d.set(12, 2, z + 2, "iron_block")
        d.set(12, 3, z + 2, "iron_trapdoor[facing=east,half=bottom,open=true,powered=false,waterlogged=false]")
    floor_rug(d, st_, 2, ("yellow_carpet", "gray_carpet"), inset=3)
    lamp_post(d, 10, 3)
    lamp_post(d, 20, 3)
    for x in range(11, 20, 2):
        d.set(x, 2, 3, "yellow_concrete" if x % 4 == 1 else "polished_blackstone_slab[type=bottom,waterlogged=false]")
    if fl == 2:
        counter(d, st_, "n", 6, 1, [P.b("smooth_quartz_slab[type=top,waterlogged=false]", "lantern[hanging=false,waterlogged=false]"),
                             P.chair("birch"), P.b("observer[facing=up,powered=false]"), P.chair("birch"),
                             P.b("lectern[facing={f},has_book=true,powered=false]")])
        rack_bay(d, st_, "w", 6, 1)
        floor_rug(d, st_, 6, ("gray_carpet",), inset=2)
        for x in range(cx + 5, 11):                                    # conveyor bridge from the tower
            for z in (cz, cz + 2):
                d.set(x, 8, z, "light_gray_concrete")
                d.set(x, 9, z, "gray_stained_glass_pane")
            d.set(x, 8, cz + 1, "smooth_quartz")
            d.set(x, 10, cz + 1, "smooth_quartz_slab[type=bottom,waterlogged=false]")
            d.set(x, 10, cz, "smooth_quartz_slab[type=bottom,waterlogged=false]")
            d.set(x, 10, cz + 2, "smooth_quartz_slab[type=bottom,waterlogged=false]")
    # ---- L3: processing hall ----
    if L >= 3:
        ph = bld(d, 22, 4, 36, 14, floors=2, fh=5, roof="flat", doors=[(22, 9, "w"), (29, 4, "n")], ribbon=True,
                 pal=dict(wall="light_gray_concrete", post="yellow_concrete", band="gray_concrete", accent="yellow_terracotta"))
        for x in range(24, 35, 3):                                    # crushers and sorting belts
            d.set(x, 2, 7, "blast_furnace[facing=south,lit=true]")
            d.set(x, 3, 7, "hopper[enabled=true,facing=down]")
            d.set(x + 1, 2, 7, "smooth_stone_slab[type=top,waterlogged=false]")
        for x in range(24, 35):
            d.set(x, 2, 11, "smooth_quartz_slab[type=top,waterlogged=false]" if x % 3 else "stonecutter[facing=north]")
        stairs_up(d, 35, 6, "south", 2, fh=5, rail=False)
        counter(d, ph, "n", 7, 1, [P.b("barrel[facing=up,open=false]", "barrel[facing=up,open=false]")] * 6)
        counter(d, ph, "s", 7, 1, [P.chair("birch"), P.b("smooth_quartz_slab[type=top,waterlogged=false]", "lantern[hanging=false,waterlogged=false]")] * 3)
        rack_bay(d, ph, "w", 7, 1)
    # ---- L4: ore silos and control tower ----
    if L >= 4:
        for i, x0 in enumerate((24, 29, 34)):
            ring = [(1, 0), (2, 0), (0, 1), (3, 1), (0, 2), (3, 2), (1, 3), (2, 3)]
            for y in range(2, 17):
                for dx, dz in ring:
                    d.set(x0 + dx, y, 17 + dz, ("light_gray_concrete", "gray_concrete")[(y // 3) % 2] if y < 16 else "yellow_concrete")
                for dx in (1, 2):
                    for dz in (1, 2):
                        d.set(x0 + dx, y, 17 + dz, ("raw_iron_block", "raw_copper_block", "coal_block")[i] if y < 15 else "smooth_quartz")
            d.set(x0 + 1, 17, 18, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        ct = bld(d, 39, 4, 44, 9, floors=4, roof="flat", doors=[(39, 7, "w")], ribbon=True,
                 pal=dict(wall="white_concrete", post="polished_deepslate", band="yellow_concrete", accent="yellow_concrete"))
        ladder(d, 43, 8, 2, 17, "west")
        for k in range(4):
            y = 2 + 4 * k
            d.set(40, y, 5, "smooth_quartz_slab[type=top,waterlogged=false]")
            d.set(41, y, 5, "observer[facing=up,powered=false]" if k % 2 else "lectern[facing=south,has_book=true,powered=false]")
            d.chair(40, y, 6, "south", "birch", sit=False)
        for z in range(15, 22):
            for x in range(22, 24):
                if (x + z) % 2:
                    d.set(x, 1, z, "yellow_concrete")
    # ---- L5: admin block, staff canteen, parking canopy with solar ----
    if L >= 5:
        ad = bld(d, 2, 22, 18, 33, floors=3, roof="flat", doors=[(10, 22, "n")], ribbon=True,
                 pal=dict(wall="white_concrete", post="gray_concrete", band="polished_deepslate", accent="yellow_concrete",
                          deck="moss_block"))
        stairs_up(d, 16, 24, "south", 2, rail=False)
        stairs_up(d, 16, 29, "north", 6, rail=False)
        d.dining(6, 2, 26, 4, "x", "birch", chairs=("n", "s"), sit=False)
        counter(d, ad, "s", 2, 1, [P.b("smoker[facing={f},lit=true]"), P.shelf("smooth_quartz", "cake[bites=0]"), P.b("water_cauldron[level=3]"),
                            P.b("barrel[facing=up,open=false]")])
        for y in (6, 10):
            for x in (4, 8, 12):
                d.set(x, y, 25, "smooth_quartz_slab[type=top,waterlogged=false]")
                d.chair(x, y, 26, "south", "birch", sit=False)
                d.set(x, y + 1, 25, "lantern[hanging=false,waterlogged=false]")
            counter(d, ad, "w", y, 1, [P.books()] * 4)
            floor_rug(d, ad, y, ("gray_carpet", "yellow_carpet"), inset=3)
        for x in range(21, 44):
            for z in range(25, 33):
                if x in (21, 43) and z in (25, 32):
                    posts(d, [(x, z)], 2, 4, "polished_deepslate")
                d.set(x, 5, z, "daylight_detector[inverted=false,power=0]" if (x + z) % 2 else "smooth_quartz_slab[type=bottom,waterlogged=false]")
        for x in range(23, 43, 3):
            d.set(x, 1, 29, "yellow_concrete")
        cart(d, 25, 27, "x", "raw_iron_block")
        cart(d, 31, 27, "x", "coal_block")
        for x in (20, 26, 32, 38):
            tree(d, x, 35, 3, "azalea_leaves", "birch_log", 1)
    paste_cluster(d, cx, cz)
    return d


@design("miner")
def miner(pack, rel, L):
    return {"Hearthwood": miner_hearthwood, "Cascadia": miner_cascadia, "Neoterra": miner_neoterra}[pack](rel, L)


# ============================================================================================ NETHER WORKER
NW_PAL = {
    "Neoterra": dict(wall="polished_blackstone", post="smooth_quartz", band="magenta_concrete", accent="magenta_concrete",
                     plinth="polished_blackstone_bricks", doorwood="crimson", floor="polished_blackstone",
                     glass="magenta_stained_glass_pane", deck="smooth_quartz"),
    "Hearthwood": dict(wall="tuff_bricks", end="tuff_bricks", framing=False, frame="stripped_dark_oak_log",
                       plinth="polished_blackstone_bricks", roof="spruce", shutter="crimson", doorwood="crimson",
                       floor="deepslate_tiles", glass="red_stained_glass_pane", chimney="tuff_bricks"),
    "Cascadia": dict(wall="dark_oak_log", siding="dark_oak_planks", batten="stripped_dark_oak_log", end="dark_oak_planks",
                     trim="red_terracotta", roof="mangrove", shutter="crimson", doorwood="crimson", plinth="blackstone",
                     floor="spruce_planks", glass="orange_stained_glass_pane", chimney="blackstone"),
}


def nw_brazier(d, x, z, pack):
    fire = "soul_campfire" if pack == "Neoterra" else "campfire"
    d.set(x, 2, z, "polished_blackstone_bricks")
    d.set(x, 3, z, f"{fire}[facing=north,lit=true,signal_fire=false,waterlogged=false]")


def netherworker_design(pack, rel, L):
    size = {"Neoterra": (52, 38, 36), "Hearthwood": (54, 38, 38), "Cascadia": (56, 38, 40)}[pack]
    d = Design(pack, rel, size, gy=1, paving={"Neoterra": "smooth_stone", "Cascadia": "coarse_dirt"}.get(pack))
    P.d = d
    d.palette = NW_PAL[pack]
    S = sty(d)
    X, Z = {"Neoterra": (16, 6), "Hearthwood": (17, 7), "Cascadia": (18, 9)}[pack]
    roof = {"Neoterra": "flat", "Hearthwood": "gable", "Cascadia": "gable"}[pack]
    axis = "z" if pack == "Hearthwood" else "x"
    W = "crimson" if pack != "Cascadia" else "dark_oak"
    big = L >= 3
    names = {"Neoterra": ["PORTAL", "LAB"], "Hearthwood": ["Shrine of the", "Ember Gate"], "Cascadia": ["EMBER", "LODGE"]}
    if not big:
        # ---- the shrine around the portal chamber (L1), narthex and vestry (L2) ----
        sh = bld(d, X + 2, Z + 6, X + 13, Z + 13, floors=1, fh=9, roof=roof, axis=axis, doors=[(X + 7, Z + 6, "n")],
                 win=3)
        d.hut(X + 3, 2, Z + 7)
        if L >= 2:
            door_cells(d).update({(X + 13, 2, Z + 10), (X + 12, 2, Z + 10)})   # keep the way to the vestry clear
        counter(d, sh, "w", 2, 2, [P.item("furnace"), P.rack()])
        counter(d, sh, "e", 2, 1, [P.item("crafting_table"), P.b("brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]"),
                            P.books(), P.b("lectern[facing={f},has_book=true,powered=false]")])
        rack_bay(d, sh, "e", 2, 1)
        counter(d, sh, "s", 2, 2, [P.books(), P.shelf("polished_blackstone_brick", "candle[candles=3,lit=false,waterlogged=false]"),
                            P.b("magma_block")])
        nw_brazier(d, X + 4, Z + 12, pack)
        nw_brazier(d, X + 11, Z + 12, pack)
        d.sign(X + 9, 4, Z + 5, "north", names[pack], W, glow=pack == "Neoterra", color="red" if pack == "Neoterra" else "black")
        for x in (X + 2, X + 13):
            lamp_post(d, x, Z + 4)
        if L >= 2:
            nx = bld(d, X + 4, Z + 1, X + 11, Z + 6, floors=2, roof=roof, axis="z" if pack != "Neoterra" else "x",
                     doors=[(X + 7, Z + 1, "n")], win=3, blind=("s",))
            d.door(X + 7, 2, Z + 6, "south", S["doorwood"])
            door_cells(d).update({(X + 7, 2, Z + 5), (X + 7, 2, Z + 7)})
            stairs_up(d, X + 10, Z + 2, "south", 2, rail=False)
            counter(d, nx, "w", 2, 1, [P.b("chest[facing={f},type=single,waterlogged=false]"), P.books(), P.chair(W)])
            counter(d, nx, "w", 6, 0, [P.books(), P.books(), P.b("lectern[facing={f},has_book=true,powered=false]")])
            counter(d, nx, "n", 6, 1, [P.chair(W), P.shelf("polished_blackstone_brick", "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]")])
            floor_rug(d, nx, 2, ("red_carpet", "black_carpet"), inset=2)
            floor_rug(d, nx, 6, ("red_carpet", "black_carpet"), inset=2)
            vs = bld(d, X + 13, Z + 8, X + 18, Z + 13, floors=1, roof=roof, axis="x", doors=[(X + 13, Z + 10, "w")],
                     blind=("w",))
            counter(d, vs, "e", 2, 0, [P.b("barrel[facing=up,open=false]", "barrel[facing=up,open=false]"),
                                P.b("chest[facing={f},type=single,waterlogged=false]"), P.b("crying_obsidian")])
            counter(d, vs, "s", 2, 1, [P.shelf("polished_blackstone_brick", "potted_crimson_fungus"), P.b("smithing_table")])
            rack_bay(d, vs, "n", 2, 1)
            flowerbed(d, X + 2, Z + 15, X + 13, Z + 16, ("crimson_roots", "warped_roots", "poppy", "wither_rose"))
    else:
        # ---- the great hall that takes the cluster's glazed gallery as its front ----
        skin = pack != "Neoterra"
        x1, x2 = (X - 1, X + 17) if skin else (X, X + 16)
        z1 = Z - 1 if skin else Z
        hl = bld(d, x1, z1, x2, Z + 13, floors=1, fh=9, roof=roof, axis=axis,
                 doors=[(X + 8, z1, "n")] if skin else [], win=3)
        d.hut(X + 3, 2, Z + 7)
        d.item(X + 2, 2, Z + 11, "blast_furnace", "east")
        d.item(X + 14, 2, Z + 11, "crafting_table")
        d.item(X + 13, 2, Z + 12, "crafting_table")
        for z in range(Z + 4, Z + 11):
            if need_racks(d):
                d.rack(X + 15, 2, z, "west")
        rack_bay(d, hl, "w", 2, 6)
        for x in (X + 5, X + 10):
            nw_brazier(d, x, Z + 6, pack)
        for x in range(X + 6, X + 10):
            d.set(x, 2, Z + 4, stair(W, "north"))
        d.rug(X + 6, Z + 5, X + 9, Z + 7, 2, ("red_carpet",), "plain")
        d.set(X + 2, 2, Z + 4, "lectern[facing=east,has_book=true,powered=false]")
        d.set(X + 12, 2, Z + 11, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
        d.set(X + 14, 2, Z + 12, "cauldron")
        for z in range(Z + 4, Z + 13, 2):
            d.set(X + 1, 2, z, "chiseled_bookshelf[facing=east,slot_0_occupied=true,slot_1_occupied=false,"
                               "slot_2_occupied=true,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")
        for x in (X + 4, X + 11):
            nw_brazier(d, x, Z + 12, pack)
        for x in range(X + 2, X + 15, 4):
            for z in (Z + 5, Z + 9):
                d.set(x, 9, z, "soul_lantern[hanging=true,waterlogged=false]" if pack == "Neoterra" else
                      "lantern[hanging=true,waterlogged=false]")
        if skin:
            d.sign(X + 6, 4, z1 - 1, "north", names[pack], W)
            if pack == "Cascadia":
                porch(d, X + 3, X + 13, z1, 3, "n", gaps=(X + 8,), ylevel=6)
        else:
            d.sign(X + 6, 9, Z - 1, "north", names[pack], W, glow=True, color="red")
        for x in (x1 - 1, x2 + 1):
            if 0 <= x < d.sx:
                lamp_post(d, x, z1 - 2 if z1 >= 2 else z1)
        # ---- L3: south annex - sacristy below, scriptorium above ----
        sa = bld(d, X + 2, Z + 13, X + 14, Z + 20, floors=2, roof=roof, axis="x", doors=[(X + 8, Z + 13, "n")],
                 blind=("n",),
                 pal={"Neoterra": dict(wall="white_concrete", post="polished_blackstone", band="magenta_terracotta"),
                      "Hearthwood": dict(wall="calcite", end="calcite", roof="dark_prismarine", framing=True),
                      "Cascadia": dict(siding="birch_planks", end="birch_planks", roof="dark_prismarine")}[pack])
        stairs_up(d, X + 3, Z + 19, "east", 2, rail=False)
        counter(d, sa, "n", 2, 1, [P.b("barrel[facing=up,open=false]", "barrel[facing=up,open=false]"),
                            P.b("chest[facing={f},type=single,waterlogged=false]"), P.b("crying_obsidian"),
                            P.shelf("polished_blackstone_brick", "potted_crimson_fungus")])
        counter(d, sa, "e", 2, 0, [P.b("smithing_table"), P.b("water_cauldron[level=3]"), P.b("magma_block")])
        counter(d, sa, "n", 6, 1, [P.books()] * 5 + [P.b("lectern[facing={f},has_book=true,powered=false]")])
        for x in (X + 6, X + 9, X + 12):
            d.set(x, 6, Z + 18, "polished_blackstone_slab[type=top,waterlogged=false]")
            d.chair(x, 6, Z + 19, "south", W, sit=False)
            d.candle(x, 7, Z + 18, 2, "red")
        floor_rug(d, sa, 2, ("black_carpet", "red_carpet"), inset=2)
        # ---- L4: east wing: library & sample laboratory over a vaulted store ----
        if L >= 4:
            ex1 = x2 + 2
            ew = bld(d, ex1, Z + 2, ex1 + 10, Z + 12, floors=3, roof=roof, axis="z" if pack == "Cascadia" else "x",
                     doors=[(ex1, Z + 7, "w"), (ex1 + 5, Z + 12, "s")],
                     pal={"Neoterra": dict(wall="white_concrete", post="polished_blackstone", band="magenta_terracotta"),
                          "Hearthwood": dict(wall="stone_bricks", end="stone_bricks", roof="deepslate_tile"),
                          "Cascadia": dict(wall="spruce_log", siding="spruce_planks", end="spruce_planks",
                                           roof="cobbled_deepslate")}[pack])
            for z in (Z + 7,):                                       # covered link to the hall
                for x in range(x2 + 1, ex1):
                    d.set(x, 1, z, S["floor"])
                    d.set(x, 4, z, slab("polished_blackstone_brick", "top"))
            d.door(x2, 2, Z + 7, "east", S["doorwood"])
            door_cells(d).update({(x2 - 1, 2, Z + 7), (x2 + 1, 2, Z + 7)})
            stairs_up(d, ex1 + 1, Z + 3, "south", 2, rail=False)
            counter(d, ew, "e", 2, 1, [P.b("barrel[facing=up,open=false]", "barrel[facing=up,open=false]")] * 4)
            counter(d, ew, "n", 2, 2, [P.b("crying_obsidian"), P.b("magma_block"), P.b("chest[facing={f},type=single,waterlogged=false]"),
                                P.b("netherrack"), P.b("soul_sand")])
            counter(d, ew, "e", 6, 1, [P.books()] * 6)
            counter(d, ew, "n", 6, 3, [P.b("lectern[facing={f},has_book=true,powered=false]"), P.chair(W),
                                P.shelf("polished_blackstone_brick", "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=true]")])
            d.dining(ex1 + 5, 6, Z + 8, 2, "x", W, chairs=("n", "s"), sit=False)
            stairs_up(d, ex1 + 9, Z + 3, "south", 6, rail=False)
            for x in range(ex1 + 2, ex1 + 9, 3):                          # observatory dormitory on the top floor
                d.bed(x, 10, Z + 11, "south")
                d.set(x + 1, 10, Z + 11, "polished_blackstone_slab[type=top,waterlogged=false]")
            counter(d, ew, "n", 10, 1, [P.b("chest[facing={f},type=single,waterlogged=false]")] * 3)
            floor_rug(d, ew, 10, ("magenta_carpet" if pack == "Neoterra" else "red_carpet",), inset=3)
            floor_rug(d, ew, 2, ("black_carpet", "red_carpet"), inset=3)
            floor_rug(d, ew, 6, ("red_carpet", "black_carpet"), inset=2)
        # ---- L5: watch tower over the gate and an ember garden ----
        if L >= 5:
            # west wing: guest cells and refectory around a small court
            wx1 = X - 13
            ww = bld(d, wx1, Z + 1, X - 3, Z + 12, floors=2, roof=roof, axis="z" if pack != "Hearthwood" else "x",
                     doors=[(X - 3, Z + 7, "e"), (wx1 + 5, Z + 1, "n")], chimney=(wx1, Z + 6),
                     pal={"Neoterra": dict(wall="white_terracotta", post="polished_blackstone", band="magenta_concrete"),
                          "Hearthwood": dict(wall="pink_terracotta", end="pink_terracotta", framing=True, roof="brick"),
                          "Cascadia": dict(siding="mangrove_planks", end="mangrove_planks", roof="deepslate_tile")}[pack])
            d.door(x1, 2, Z + 7, "west", S["doorwood"])
            for x in range(X - 2, x1):
                d.set(x, 1, Z + 7, S["floor"])
            door_cells(d).update({(x1 + 1, 2, Z + 7), (x1 - 1, 2, Z + 7), (X - 2, 2, Z + 7)})
            d.hearth(wx1 + 1, 2, Z + 6, "east", 5, S["chimney"], "campfire")
            d.dining(wx1 + 4, 2, Z + 8, 4, "z", W, chairs=("e", "w"), sit=False)
            counter(d, ww, "n", 2, 2, [P.b("smoker[facing={f},lit=true]"), P.b("water_cauldron[level=3]"),
                                P.b("barrel[facing=up,open=false]", "barrel[facing=up,open=false]")])
            stairs_up(d, X - 4, Z + 11, "north", 2, rail=False)
            for z in (Z + 2, Z + 5, Z + 8, Z + 11):
                d.bed(wx1 + 1, 6, z, "west")
                if z < Z + 11:
                    d.set(wx1 + 1, 6, z + 1, "polished_blackstone_slab[type=top,waterlogged=false]")
            floor_rug(d, ww, 6, ("red_carpet", "black_carpet"), inset=3)
            for x in range(wx1, X - 2, 3):
                lamp_post(d, x, Z + 15)
            for x in range(wx1 + 1, X - 3, 3):
                tree(d, x, Z + 18, 4, None, None, 1)
            tx = x2 + 2
            tw = bld(d, tx, Z + 15, tx + 5, Z + 20, floors=6, roof="hip" if pack != "Neoterra" else "flat", axis="x",
                     doors=[(tx, Z + 17, "w")], win=2,
                     pal={"Neoterra": dict(wall="polished_blackstone_bricks", post="smooth_quartz", band="magenta_concrete"),
                          "Hearthwood": dict(roof="deepslate_tile"), "Cascadia": dict(roof="cobbled_deepslate")}[pack])
            ladder(d, tx + 4, Z + 19, 2, 25, "west")
            for k in range(6):
                y = 2 + 4 * k
                d.set(tx + 1, y, Z + 16, "lectern[facing=south,has_book=true,powered=false]" if k % 2 else "chiseled_bookshelf[facing=south,slot_0_occupied=true,slot_1_occupied=true,slot_2_occupied=false,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")
                d.set(tx + 2, y, Z + 16, "barrel[facing=up,open=false]")
                d.set(tx + 1, y + 2, Z + 18, "soul_lantern[hanging=true,waterlogged=false]")
            gx1, gz1 = X, Z + 22
            for x in range(gx1, gx1 + 15):
                for z in range(gz1, gz1 + 5):
                    edge = x in (gx1, gx1 + 14) or z in (gz1, gz1 + 4)
                    if edge:
                        d.set(x, 2, z, "polished_blackstone_brick_wall" if (x + z) % 4 else "polished_blackstone_bricks")
                    else:
                        d.set(x, 1, z, ("crimson_nylium", "warped_nylium", "soul_soil")[(x + z) % 3])
                        if (x + z) % 3 == 0:
                            d.set(x, 2, z, ("crimson_fungus", "warped_fungus", "crimson_roots", "warped_roots")[(x * 7 + z) % 4])
            for x in (gx1 + 3, gx1 + 11):
                nw_brazier(d, x, gz1 + 2, pack)
            d.set(gx1 + 7, 2, gz1 + 2, "lodestone")
            d.set(gx1 + 7, 2, gz1, AIR)
            for x in (gx1 - 2, gx1 + 16):
                if 0 <= x < d.sx:
                    lamp_post(d, x, gz1 + 2)
        paste_cluster(d, X, Z)
        return d
    paste_cluster(d, X + 5, Z + 8)
    return d


@design("netherworker")
def netherworker(pack, rel, L):
    return netherworker_design(pack, rel, L)



# ================================================================================================ FISHERMAN
def fish_core(d, r, wood, smoker_side="s", rack_side="w", u0=1, ru0=2):
    """The hut's work blocks in the main room: smoker, crafting table, bait barrel, racks."""
    counter(d, r, smoker_side, 2, u0, [P.item("smoker"), P.item("crafting_table"), P.item("barrel")])
    rack_bay(d, r, rack_side, 2, ru0, min(2, need_racks(d)))


def fish_stall(d, x1, x2, z, wood, awning=("white_wool", "cyan_wool")):
    """Market stall: counter with ice and fish barrels, striped awning on posts."""
    for x in range(x1, x2 + 1):
        d.set(x, 2, z, f"{wood}_slab[type=top,waterlogged=false]")
        d.set(x, 3, z, "packed_ice" if x % 2 else "barrel[facing=north,open=false]")
        d.set(x, 5, z, awning[x % 2])
        d.set(x, 5, z - 1, awning[x % 2])
    posts(d, [(x1 - 1, z - 1), (x2 + 1, z - 1)], 2, 5, f"{wood}_fence")


def fisherman_neoterra(rel, L):
    d = Design("Neoterra", rel, (46, 30, 34), gy=1, paving="smooth_stone")
    P.d = d
    d.palette = dict(wall="white_concrete", post="light_gray_concrete", band="cyan_terracotta", accent="cyan_concrete",
                     doorwood="birch", deck="smooth_quartz")
    cx, cz = 20, 2                                                    # pond 20..32 x 2..18, pier rows 9..10
    fl = 1 if L == 1 else 2
    of = bld(d, 10, 5, 19, 13, floors=fl, roof="flat", doors=[(19, 9, "e"), (19, 10, "e"), (14, 5, "n")], ribbon=True)
    if fl == 2:
        stairs_up(d, 12, 12, "east", 2, rail=False)
    d.hut(11, 2, 6)
    fish_core(d, of, "birch", u0=0)
    counter(d, of, "n", 2, 4, [P.b("barrel[facing=up,open=false]", "barrel[facing=up,open=false]"), P.shelf("smooth_quartz", "potted_bamboo")])
    d.set(15, 2, 9, "smooth_quartz_slab[type=top,waterlogged=false]")      # chart table
    d.set(15, 3, 9, "lantern[hanging=false,waterlogged=false]")
    d.chair(15, 2, 8, "north", "birch", sit=False)
    d.chair(14, 2, 9, "west", "birch", sit=False)
    floor_rug(d, of, 2, ("cyan_carpet", "white_carpet"), inset=3)
    d.sign(14, 5, 4, "north", ["HARBOUR", "MASTER"], "birch", glow=True, color="cyan")
    lamp_post(d, 9, 3)
    lamp_post(d, 19, 3)
    bench(d, 11, 2, "north", 2)
    for x in range(10, 20):
        d.set(x, 1, 3, "light_gray_concrete") if x % 2 else None
    if fl == 2:
        counter(d, of, "n", 6, 1, [P.b("lectern[facing={f},has_book=true,powered=false]"), P.b("cartography_table"), P.chair("birch"),
                            P.shelf("smooth_quartz", "potted_fern"), P.books()])
        counter(d, of, "w", 6, 1, [P.rack()] * min(2, need_racks(d)) + [P.shelf("smooth_quartz", "candle[candles=2,lit=false,waterlogged=false]")])
        floor_rug(d, of, 6, ("light_gray_carpet", "cyan_carpet"), inset=2)
        for x in range(8, 20, 3):                                       # street planters
            d.set(x, 2, 1, "moss_block")
            d.set(x, 3, 1, "azalea" if x % 2 else "flowering_azalea")
            d.set(x + 1, 2, 1, "smooth_quartz_slab[type=bottom,waterlogged=false]")
        # south deck with tables
        d.fill(10, 1, 15, 19, 1, 19, "mangrove_planks")
        for x in range(10, 20):
            d.set(x, 2, 19, "white_stained_glass_pane")
        for x in range(10, 20):                                         # pergola over the deck
            for z in (15, 17, 19):
                d.set(x, 6, z, "birch_slab[type=bottom,waterlogged=false]")
        for z in range(15, 20):
            d.set(10, 6, z, "stripped_birch_log[axis=z]")
            d.set(19, 6, z, "stripped_birch_log[axis=z]")
        posts(d, [(10, 19), (19, 19), (14, 19)], 3, 5, "stripped_birch_log[axis=y]")
        for x in (11, 18):
            d.set(x, 2, 18, "moss_block")
            d.set(x, 3, 18, "flowering_azalea")
        for x in range(10, 19, 4):                                      # quay lamps and benches by the pier gate
            lamp_post(d, x, 21)
            bench(d, x + 1, 21, "south", 2)
        flowerbed(d, 1, 19, 7, 20, ("cornflower", "white_tulip", "azure_bluet"))
        for x in (12, 16):
            d.chair(x - 1, 2, 17, "west", "birch", sit=False)
            d.table(x, 2, 17, "birch", "slab", "smooth_quartz_slab")
            d.chair(x + 1, 2, 17, "east", "birch", sit=False)
            d.set(x, 5, 17, "smooth_quartz_slab[type=top,waterlogged=false]")
    # ---- L3: fish market & sushi bar (two storeys, glazed front) ----
    if L >= 3:
        mk = bld(d, 1, 4, 8, 17, floors=2, roof="flat", doors=[(4, 4, "n"), (8, 9, "e")], ribbon=True,
                 pal=dict(wall="white_terracotta", post="orange_terracotta", band="orange_concrete",
                          accent="orange_concrete", plinth="polished_andesite"))
        for z in (7, 11, 15):
            for x in range(2, 7):
                d.set(x, 2, z, "smooth_quartz_slab[type=top,waterlogged=false]" if x != 4 else "blue_ice")
            d.set(3, 3, z, "packed_ice")
            d.set(5, 3, z, "barrel[facing=north,open=false]")
        stairs_up(d, 7, 16, "north", 2, rail=False)
        for z in range(6, 12):
            d.set(2, 6, z, "smooth_quartz_slab[type=top,waterlogged=false]")
            d.chair(3, 6, z, "east", "birch", sit=False)
        counter(d, mk, "s", 6, 0, [P.b("smoker[facing={f},lit=true]"), P.shelf("smooth_quartz", "potted_bamboo"), P.b("water_cauldron[level=3]")])
        floor_rug(d, mk, 6, ("orange_carpet", "white_carpet"), inset=3)
        rack_bay(d, of, "w", 2, 2)
        rack_bay(d, mk, "e", 6, 4)
        d.sign(4, 5, 3, "north", ["FISH", "MARKET"], "birch", glow=True, color="orange")
        for x in (2, 6):
            d.set(x, 5, 3, "orange_concrete")
    # ---- L4: cold store & processing building ----
    if L >= 4:
        cs = bld(d, 2, 21, 18, 29, floors=2, roof="flat", doors=[(10, 21, "n")], ribbon=True,
                 pal=dict(wall="light_gray_concrete", post="gray_concrete", band="cyan_concrete", plinth="gray_concrete",
                          accent="cyan_terracotta"))
        for x in range(4, 17, 2):
            d.set(x, 2, 25, "smooth_quartz_slab[type=top,waterlogged=false]")
            d.set(x + 1, 2, 25, "smooth_quartz_slab[type=top,waterlogged=false]")
            d.set(x, 3, 25, "water_cauldron[level=3]" if x % 4 == 0 else "packed_ice")
        counter(d, cs, "s", 2, 0, [P.b("blue_ice", "packed_ice")] * 8)
        counter(d, cs, "w", 2, 0, [P.b("barrel[facing=up,open=false]", "barrel[facing=up,open=false]")] * 3)
        stairs_up(d, 15, 22, "south", 2, rail=False)
        counter(d, cs, "s", 6, 0, [P.b("barrel[facing=up,open=false]")] * 6 + [P.b("chest[facing={f},type=single,waterlogged=false]")])
        counter(d, cs, "w", 6, 0, [P.b("lectern[facing={f},has_book=true,powered=false]"), P.chair("birch"), P.books()])
        floor_rug(d, cs, 6, ("light_gray_carpet",), inset=3)
        for x in range(4, 17, 4):
            for z in (23, 27):
                d.set(x, 11, z, "daylight_detector[inverted=false,power=0]")
    # ---- L5: boat hall east of the pond, lighthouse, promenade ----
    if L >= 5:
        bh = bld(d, 35, 3, 44, 15, floors=2, fh=5, roof="flat", doors=[(35, 9, "w"), (35, 10, "w")], ribbon=True,
                 pal=dict(wall="mangrove_planks", post="white_concrete", band="white_concrete", accent="orange_concrete"))
        for x in range(37, 43):
            d.set(x, 2, 6, "birch_slab[type=top,waterlogged=false]")
            d.set(x, 2, 12, "birch_slab[type=top,waterlogged=false]")
        for x in range(37, 43, 2):
            d.set(x, 3, 6, "birch_trapdoor[facing=south,half=bottom,open=false,powered=false,waterlogged=false]")
            d.set(x, 3, 12, "birch_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
        counter(d, bh, "e", 2, 0, [P.b("barrel[facing=up,open=false]", "chain[axis=y,waterlogged=false]")] * 4)
        stairs_up(d, 43, 13, "north", 2, fh=5, rail=False)
        counter(d, bh, "w", 7, 2, [P.chair("birch"), P.b("smooth_quartz_slab[type=top,waterlogged=false]", "potted_bamboo"), P.chair("birch")])
        lh = bld(d, 36, 21, 40, 25, floors=5, roof="flat", doors=[(38, 21, "n")], win=2,
                 wallfn=lambda x, y, z, rel, c, a, k: "red_concrete" if (y // 4) % 2 else "white_concrete")
        for y in range(2, 22):
            d.set(39, y, 24, "ladder[facing=west,waterlogged=false]") if y < 22 else None
        d.fill(37, 22, 22, 39, 22, 24, "sea_lantern")
        d.fill(37, 23, 22, 39, 23, 24, "light_blue_stained_glass")
        d.set(38, 24, 23, "smooth_quartz_slab[type=bottom,waterlogged=false]")
        for z in range(20, 33):
            if z % 3 == 0:
                lamp_post(d, 33, z)
        for x in range(21, 32, 4):
            bench(d, x, 22, "south", 2)
            bench(d, x, 30, "north", 2)
        for x in (22, 27, 31):
            tree(d, x, 26, 4, "azalea_leaves", "birch_log", 1)
    paste_cluster(d, cx, cz)
    return d


def fisherman_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (46, 30, 40), gy=1)
    P.d = d
    d.palette = dict(wall="light_blue_terracotta", end="light_blue_terracotta", frame="stripped_dark_oak_log",
                     roof="dark_prismarine", shutter="birch", doorwood="crimson", plinth="cobblestone")
    cx, cz = 22, 2                                                    # pond 22..34 x 2..18, pier rows 9..10
    fl = 1 if L == 1 else 2
    ct = bld(d, 13, 5, 21, 13, floors=fl, axis="z", doors=[(21, 9, "e"), (21, 10, "e"), (16, 5, "n")], chimney=(13, 10))
    d.hut(14, 2, 6)
    d.hearth(14, 2, 10, "east", 5, "bricks", "campfire")
    fish_core(d, ct, "dark_oak", "s", "n", ru0=4)
    for x in range(17, 20):
        if x != 18:
            d.set(x, 2, 8, "dark_oak_slab[type=top,waterlogged=false]")
    d.set(17, 3, 8, "packed_ice")
    floor_rug(d, ct, 2, inset=3)
    d.sign(17, 4, 4, "north", ["The Silver", "Herring"], "dark_oak")
    lamp_post(d, 12, 3)
    bench(d, 18, 3, "north", 2)
    if fl == 2:
        stairs_up(d, 20, 12, "north", 2, rail=False)
        d.bed(14, 6, 6, "north")
        counter(d, ct, "w", 6, 2, [P.b("chest[facing={f},type=single,waterlogged=false]"), P.books(), P.b("barrel[facing=up,open=false]")])
        counter(d, ct, "s", 6, 0, [P.rack()] * min(2, need_racks(d)) + [P.shelf("dark_oak", "candle[candles=3,lit=false,waterlogged=false]")])
        for x in range(15, 20):
            d.set(x, 8, 6, "cobweb") if x % 2 else None
        floor_rug(d, ct, 6, inset=2)
        # brick smokehouse
        sm = bld(d, 13, 16, 17, 20, floors=1, fh=5, roof="hip", doors=[(15, 16, "n")],
                 wallfn=lambda x, y, z, rel, c, a, k: "bricks", win=99)
        d.set(14, 2, 19, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        d.set(16, 2, 19, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        for x in (14, 15, 16):
            for z in (18, 19):
                d.set(x, 5, z, CHAIN)
                d.set(x, 4, z, "dried_kelp_block")
        for y in range(7, 11):
            d.set(15, y, 18, "bricks")
        d.set(15, 11, 18, "brick_slab[type=bottom,waterlogged=false]")
    # ---- L3: timber market hall (open ground floor, room above) ----
    if L >= 3:
        mk = bld(d, 2, 4, 11, 14, floors=2, axis="x", doors=[(6, 4, "n")],
                 pal=dict(wall="white_terracotta", end="white_terracotta", roof="deepslate_tile", frame="stripped_oak_log",
                          plinth="stone_bricks", shutter="warped"))
        for y in range(2, 5):                                           # open arcade below
            for x in range(3, 11):
                for z in (4, 14):
                    if x % 3:
                        d.set(x, y, z, AIR)
            for z in range(5, 14):
                if z % 3:
                    d.set(2, y, z, AIR)
        door_cells(d).update({(x, 2, z) for x in range(3, 11) for z in (3, 5, 13, 15)})
        fish_stall(d, 4, 6, 8, "dark_oak", ("white_wool", "red_wool"))
        fish_stall(d, 8, 10, 11, "dark_oak", ("white_wool", "red_wool"))
        ladder(d, 10, 6, 2, 5, "west")
        d.set(10, 5, 6, AIR)
        ladder(d, 10, 6, 2, 5, "west")
        counter(d, mk, "s", 6, 0, [P.b("barrel[facing=up,open=false]", "barrel[facing=up,open=false]")] * 3 + [P.books()] * 2)
        counter(d, mk, "w", 6, 0, [P.b("lectern[facing={f},has_book=true,powered=false]"), P.chair("dark_oak")])
        rack_bay(d, mk, "n", 6, 2)
        floor_rug(d, mk, 6, inset=3)
    # ---- L4: boathouse with net loft along the pond's south side ----
    if L >= 4:
        bt = bld(d, 22, 21, 34, 28, floors=2, axis="x", doors=[(28, 21, "n")], chimney=(34, 25),
                 pal=dict(wall="dark_oak_planks", end="dark_oak_planks", framing=False, roof="spruce",
                          frame="dark_oak_log", plinth="stone_bricks", shutter="spruce"))
        for z in (23, 26):
            for x in range(24, 33):
                d.set(x, 2, z, "dark_oak_slab[type=top,waterlogged=false]" if x % 4 else "dark_oak_fence")
        for x in range(24, 33, 2):
            d.set(x, 3, 23, "dark_oak_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
            d.set(x, 3, 26, "dark_oak_trapdoor[facing=south,half=bottom,open=false,powered=false,waterlogged=false]")
        stairs_up(d, 23, 27, "east", 2, rail=False)
        for x in range(24, 34):
            for z in (22, 23):
                if (x + z) % 2:
                    d.set(x, 8, z, "cobweb")
        counter(d, bt, "s", 6, 5, [P.b("barrel[facing=up,open=false]")] * 3 + [P.b("chest[facing={f},type=single,waterlogged=false]")])
        for x in range(22, 35, 3):
            d.set(x, 2, 30, "dark_oak_fence")
            d.set(x, 3, 30, "dark_oak_fence")
        for x in range(22, 35):
            if x % 3:
                d.set(x, 3, 30, "cobweb")
        flowerbed(d, 2, 17, 11, 19)
        nm = bld(d, 2, 22, 9, 29, floors=2, axis="z", doors=[(5, 22, "n")], chimney=(9, 26),
                 pal=dict(wall="pink_terracotta", end="pink_terracotta", roof="brick", frame="stripped_oak_log",
                          shutter="birch", doorwood="oak"))
        d.hearth(8, 2, 26, "west", 5, "bricks", "campfire")
        counter(d, nm, "w", 2, 1, [P.b("loom[facing={f}]"), P.chair("oak"), P.b("barrel[facing=up,open=false]", "white_wool"),
                            P.b("chest[facing={f},type=single,waterlogged=false]")])
        stairs_up(d, 4, 28, "east", 2, rail=False)
        d.bed(3, 6, 23, "north")
        counter(d, nm, "e", 6, 0, [P.b("chest[facing={f},type=single,waterlogged=false]"), P.books()])
        floor_rug(d, nm, 2, inset=2)
    # ---- L5: harbourmaster's house, harbour light, quay crane ----
    if L >= 5:
        hm_ = bld(d, 37, 3, 44, 12, floors=2, axis="z", doors=[(40, 3, "n")], chimney=(44, 8),
                  pal=dict(wall="yellow_terracotta", end="yellow_terracotta", roof="dark_prismarine",
                           frame="stripped_oak_log", shutter="warped", doorwood="oak"))
        d.hearth(43, 2, 8, "west", 5, "bricks", "campfire")
        counter(d, hm_, "w", 2, 1, [P.books(), P.books(), P.b("lectern[facing={f},has_book=true,powered=false]"), P.chair("dark_oak")])
        d.dining(40, 2, 8, 2, "z", "oak", chairs=("e", "w"), sit=False)
        stairs_up(d, 38, 11, "north", 2, rail=False)
        d.bed(43, 6, 4, "north")
        counter(d, hm_, "s", 6, 0, [P.b("chest[facing={f},type=single,waterlogged=false]"), P.b("barrel[facing=up,open=false]"), P.books()])
        floor_rug(d, hm_, 2, inset=3)
        floor_rug(d, hm_, 6, inset=2)
        lt = bld(d, 38, 16, 42, 20, floors=4, roof="hip", doors=[(40, 16, "n")], win=2,
                 wallfn=lambda x, y, z, rel, c, a, k: "white_terracotta" if (y // 3) % 2 else "red_terracotta")
        ladder(d, 41, 19, 2, 17, "west")
        d.set(40, 17, 18, "lantern[hanging=false,waterlogged=false]")
        # quay crane
        posts(d, [(36, 23)], 2, 9, "dark_oak_log[axis=y]")
        for x in range(33, 37):
            d.set(x, 9, 23, "stripped_dark_oak_log[axis=x]")
        for y in range(5, 9):
            d.set(33, y, 23, CHAIN)
        d.set(33, 4, 23, "barrel[facing=up,open=false]")
        for x, z in ((13, 33), (17, 36), (8, 36), (2, 36), (21, 36), (44, 30), (40, 36), (44, 36)):
            tree(d, x, z, 4, "oak_leaves")
        # chandlery: ship's supplies shop on the quay
        ch = bld(d, 24, 32, 33, 38, floors=1, axis="x", doors=[(28, 32, "n")], chimney=(33, 35),
                 pal=dict(wall="bricks", end="bricks", framing=False, roof="mud_brick", frame="stripped_spruce_log",
                          shutter="mangrove", doorwood="spruce", plinth="stone_bricks"))
        counter(d, ch, "s", 2, 0, [P.b("barrel[facing=up,open=false]", "barrel[facing=up,open=false]"),
                            P.shelf("spruce", "lantern[hanging=false,waterlogged=false]"), P.b("chest[facing={f},type=single,waterlogged=false]"),
                            P.b("barrel[facing=up,open=false]", "white_wool"), P.shelf("spruce", "decorated_pot[cracked=false,facing=north,waterlogged=false]"),
                            P.b("cartography_table")])
        for x in range(26, 32):
            if x != 29:
                d.set(x, 2, 34, "spruce_slab[type=top,waterlogged=false]")
        d.set(27, 3, 34, "candle[candles=2,lit=false,waterlogged=false]")
        floor_rug(d, ch, 2, inset=2)
        fish_stall(d, 26, 28, 30, "spruce", ("white_wool", "blue_wool"))
        for x in range(2, 21, 4):
            lamp_post(d, x, 25) if x != 6 else None
        bench(d, 8, 24, "north", 3)
        cart(d, 15, 25, "x", "hay_block[axis=y]")
    paste_cluster(d, cx, cz)
    return d


def fisherman_cascadia(rel, L):
    d = Design("Cascadia", rel, (48, 30, 40), gy=1, paving="coarse_dirt")
    P.d = d
    d.palette = dict(wall="birch_planks", siding="birch_planks", batten="stripped_spruce_log", end="birch_planks",
                     roof="dark_prismarine", shutter="warped", doorwood="spruce", plinth="andesite")
    cx, cz = 24, 3                                                    # pond 24..36 x 3..19, pier rows 10..11
    fl = 1 if L < 3 else 2
    bh = bld(d, 14, 6, 23, 15, floors=fl, axis="x", doors=[(17, 6, "n")])
    for z in (10, 11):                                                # boat doors onto the pier
        for y in (2, 3, 4):
            d.set(23, y, z, AIR)
        door_cells(d).update({(22, 2, z), (24, 2, z)})
    if fl == 2:
        stairs_up(d, 15, 9, "south", 2, rail=False)
    d.hut(15, 2, 7)
    fish_core(d, bh, "spruce", "n", "s", u0=4)
    for x in range(17, 21):                                           # canoe on trestles
        d.set(x, 3, 12, "spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    d.set(17, 2, 12, "spruce_fence")
    d.set(20, 2, 12, "spruce_fence")
    counter(d, bh, "w", 2, 1, [P.b("barrel[facing=up,open=false]", "barrel[facing=up,open=false]"), P.shelf("spruce", "lantern[hanging=false,waterlogged=false]")])
    d.sign(19, 4, 5, "north", ["SALMON RUN", "Fish Camp"], "spruce")
    lamp_post(d, 13, 4)
    woodpile(d, 14, 17, 3)
    tree(d, 2, 3, 6, "spruce_leaves", "spruce_log", 2)
    if L >= 2:
        porch(d, 14, 23, 6, 3, "n", gaps=(17,))
        sk = bld(d, 14, 19, 18, 23, floors=1, axis="z", doors=[(16, 19, "n")], chimney=(16, 23))
        d.set(16, 2, 22, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        for x in (15, 17):
            for z in (21, 22):
                d.set(x, 4, z, "dried_kelp_block")
        rack_bay(d, bh, "w", 2, 3)
        rack_bay(d, bh, "e", 2, 0)
        for z in range(22, 27):                                       # fish drying racks
            d.set(21, 2, z, "spruce_fence")
            d.set(21, 4, z, "spruce_fence")
            d.set(21, 3, z, "dried_kelp_block" if z % 2 else "cobweb")
        for x in range(19, 24):                                       # gutting table under a shelter
            for z in (17, 18, 19):
                d.set(x, 5, z, "spruce_slab[type=bottom,waterlogged=false]")
        posts(d, [(19, 17), (23, 17), (19, 19), (23, 19)], 2, 4, "spruce_log[axis=y]")
        for x in (20, 21, 22):
            d.set(x, 2, 19, "spruce_slab[type=top,waterlogged=false]")
        d.set(21, 3, 19, "packed_ice")
        d.set(22, 2, 17, "barrel[facing=up,open=false]")
        fx, fz = 28, 27                                               # camp fire ring with log benches
        d.set(fx, 2, fz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        for dx, dz in ((-1, -1), (0, -1), (1, -1), (-1, 1), (0, 1), (1, 1), (-1, 0), (1, 0)):
            d.set(fx + dx, 1, fz + dz, "cobblestone")
        for dx in (-1, 0, 1):
            d.set(fx + dx, 2, fz - 3, "stripped_spruce_log[axis=x]")
            d.set(fx + dx, 2, fz + 3, "stripped_spruce_log[axis=x]")
        for dz in (-1, 0, 1):
            d.set(fx - 3, 2, fz + dz, "stripped_spruce_log[axis=z]")
            d.set(fx + 3, 2, fz + dz, "stripped_spruce_log[axis=z]")
        lamp_post(d, 32, 25)
        tree(d, 32, 31, 6, "spruce_leaves", "spruce_log", 2)
        woodpile(d, 24, 30, 4)
        oh = bld(d, 44, 14, 46, 16, floors=1, axis="x", doors=[(45, 14, "n")], win=9, lamps=False,
                 pal=dict(wall="spruce_planks", siding="spruce_planks", batten="stripped_spruce_log", roof="spruce"))
        d.set(45, 2, 15, "spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
        lamp_post(d, 24, 22)
        lamp_post(d, 13, 17)
        bench(d, 25, 25, "west", 2)
    if fl == 2:
        counter(d, bh, "n", 6, 2, [P.b("barrel[facing=up,open=false]")] * 2 + [P.rack()] * min(2, need_racks(d)) +
            [P.b("chest[facing={f},type=single,waterlogged=false]")])
        for x in range(17, 23):
            for z in (13, 14):
                if (x + z) % 2:
                    d.set(x, 8, z, "cobweb")
        d.bed(22, 6, 7, "north")
        floor_rug(d, bh, 6, inset=3)
    # ---- L3: ice house (sawdust-packed ice) ----
    if L >= 3:
        ih = bld(d, 39, 4, 46, 11, floors=1, fh=5, axis="z", doors=[(39, 8, "w")],
                 pal=dict(wall="dark_oak_log", siding="dark_oak_planks", batten="stripped_dark_oak_log",
                          end="dark_oak_planks", roof="mangrove", shutter="dark_oak", plinth="mossy_cobblestone"))
        for x in range(41, 46):
            for z in range(5, 11):
                if x > 42 or z in (5, 10):
                    d.set(x, 2, z, "packed_ice" if (x + z) % 3 else "blue_ice")
                    if (x + z) % 2 and x > 43:
                        d.set(x, 3, z, "packed_ice")
        d.set(40, 2, 6, "barrel[facing=up,open=false]")
        d.set(40, 2, 10, "barrel[facing=up,open=false]")
        d.set(40, 3, 10, "brown_wool")
        cart(d, 37, 13, "z", "packed_ice")
        lamp_post(d, 38, 5)
    # ---- L4: cannery ----
    if L >= 4:
        cn = bld(d, 2, 5, 11, 22, floors=2, axis="z", doors=[(11, 9, "e"), (6, 5, "n")], chimney=(2, 14),
                 pal=dict(wall="mangrove_planks", siding="mangrove_planks", batten="stripped_dark_oak_log",
                          end="mangrove_planks", roof="spruce", shutter="spruce", plinth="cobblestone"))
        for z in range(8, 21, 3):
            for x in range(4, 9):
                d.set(x, 2, z, "spruce_slab[type=top,waterlogged=false]")
            d.set(5, 3, z, "packed_ice")
            d.set(7, 3, z, "barrel[facing=north,open=false]")
        counter(d, cn, "e", 2, 6, [P.b("barrel[facing=up,open=false]", "barrel[facing=up,open=false]")] * 4)
        d.hearth(3, 2, 14, "east", 5, "cobblestone", "campfire")
        stairs_up(d, 10, 20, "north", 2, rail=False)
        rack_bay(d, cn, "w", 6, 1)
        counter(d, cn, "w", 6, 1, [P.b("barrel[facing=up,open=false]")] * 4)
        for z in (8, 11, 14):
            d.bed(9, 6, z, "east")
        floor_rug(d, cn, 6, inset=3)
        cart(d, 13, 18, "z", "hay_block[axis=y]")
    # ---- L5: bunkhouse, lookout tower, canoe racks ----
    if L >= 5:
        bk = bld(d, 2, 26, 12, 33, floors=2, axis="x", doors=[(7, 26, "n")], chimney=(12, 30),
                 pal=dict(wall="spruce_log", siding="spruce_planks", batten="stripped_spruce_log", end="spruce_planks",
                          roof="deepslate_tile", shutter="mangrove", plinth="tuff"))
        for x in (3, 5, 7, 9):
            d.bed(x, 2, 32, "south")
            d.bed(x, 6, 32, "south")
        d.set(11, 2, 30, "campfire[facing=west,lit=true,signal_fire=false,waterlogged=false]")
        stairs_up(d, 3, 28, "east", 2, rail=False)
        counter(d, bk, "n", 2, 6, [P.b("chest[facing={f},type=single,waterlogged=false]")] * 2)
        d.dining(8, 2, 29, 2, "x", "spruce", chairs=("n",), sit=False)
        floor_rug(d, bk, 6, inset=3)
        lk = bld(d, 39, 24, 43, 28, floors=4, axis="x", doors=[(41, 24, "n")], win=2)
        ladder(d, 42, 27, 2, 17, "west")
        for x in range(26, 36, 3):
            d.set(x, 2, 23, "spruce_fence")
            d.set(x, 3, 23, "spruce_fence")
            d.set(x + 1, 3, 23, "stripped_spruce_log[axis=x]")
            d.set(x + 2, 3, 23, "stripped_spruce_log[axis=x]")
        for x, z in ((20, 32), (26, 34), (38, 34), (44, 33), (16, 36), (46, 38), (21, 38), (33, 37), (14, 30)):
            tree(d, x, z, 6, "spruce_leaves", "spruce_log", 2)
        porch(d, 2, 12, 26, 2, "n", gaps=(7,))
    paste_cluster(d, cx, cz)
    return d


@design("fisherman")
def fisherman(pack, rel, L):
    return {"Hearthwood": fisherman_hearthwood, "Cascadia": fisherman_cascadia,
            "Neoterra": fisherman_neoterra}[pack](rel, L)


# =============================================================================================== PLANTATION
def gambrel(d, x1, z1, x2, z2, y0, stairs, block, end, overhang=1):
    """Barn roof (ridge along z): steep lower slope, gentle upper slope. Wall tops at y0-1. Returns ridge y."""
    a1, a2 = x1 - overhang, x2 + overhang
    n = a2 - a1 + 1
    half = n // 2
    prof = [0, 2, 4, 5, 6, 7, 7, 8, 8, 9][:half]
    for i in range(half):
        for side in (0, 1):
            x = a1 + i if side == 0 else a2 - i
            face = "east" if side == 0 else "west"
            h = y0 + prof[i] - overhang
            top_cell = (i == half - 1 and n % 2 == 0)
            for z in range(z1 - overhang, z2 + overhang + 1):
                if top_cell:
                    d.set(x, h, z, block)
                else:
                    d.set(x, h, z, stair(stairs, face))
                lo = y0 + prof[i - 1] - overhang + 1 if i > 0 else h
                for y in range(lo, h):
                    d.set(x, y, z, block)
            # gable ends
            if x1 <= x <= x2:
                for z in (z1, z2):
                    for y in range(y0, h):
                        if d.air(x, y, z):
                            d.set(x, y, z, end)
    if n % 2 == 1:
        x = a1 + half
        h = y0 + prof[half - 1] - overhang + 1
        for z in range(z1 - overhang, z2 + overhang + 1):
            d.set(x, h, z, slab(stairs))
        for z in (z1, z2):
            for y in range(y0, h):
                if d.air(x, y, z):
                    d.set(x, y, z, end)
    return y0 + prof[half - 1] - overhang


def planter_row(d, x1, x2, z, y, crops=("wheat[age=7]", "carrots[age=7]", "potatoes[age=7]", "beetroots[age=3]")):
    for i, x in enumerate(range(x1, x2 + 1)):
        d.set(x, y - 1, z, "farmland[moisture=7]")
        d.set(x, y, z, crops[(i // 2) % len(crops)])


def lean_glass(d, xa, xb, za, zb, ends=(True, True)):
    """Victorian lean-to glasshouse along x: brick back wall at za (street), glass slope down to a low brick wall at
    zb (south, toward the beds). Inside: a staging bench along the back wall and an aisle."""
    depth = zb - za                                                   # rows za+1..zb
    top = 4 + depth                                                   # back wall height
    for x in range(xa, xb + 1):
        for y in range(2, top + 1):
            d.set(x, y, za, "bricks")
        d.set(x, top + 1, za, slab("brick"))
        for i, z in enumerate(range(zb, za, -1)):
            ry = 5 + i
            d.set(x, ry, z, "glass" if x % 3 else stair("dark_oak", "north"))
            for y in range(2, ry):
                if z == zb:
                    d.set(x, y, z, "bricks" if y == 2 else "glass_pane")
                else:
                    d.set(x, y, z, AIR)
    for x, on in ((xa, ends[0]), (xb, ends[1])):
        if not on:
            continue
        for i, z in enumerate(range(zb, za, -1)):
            for y in range(2, 5 + i):
                d.set(x, y, z, "bricks")
    d.fill(xa, 1, za + 1, xb, 1, zb - 1, "bricks")
    for x in range(xa + 1, xb):                                      # staging bench with seedlings
        if d.air(x, 2, za + 1):
            d.set(x, 2, za + 1, "dark_oak_slab[type=top,waterlogged=false]")
            d.set(x, 3, za + 1, ("potted_cactus", "potted_fern", "potted_bamboo", "potted_red_tulip")[x % 4])
    d.fill(xa, 2 + 0, za, xb, 2, za, "bricks")


def plantation_neoterra(rel, L):
    d = Design("Neoterra", rel, (42, 26, 34), gy=1, paving="smooth_stone")
    P.d = d
    d.palette = dict(wall="light_gray_concrete", post="orange_terracotta", band="white_concrete", accent="orange_concrete",
                     plinth="polished_andesite", deck="moss_block", doorwood="mangrove")
    fl = 1 if L == 1 else 2
    of = bld(d, 27, 1, 35, 8, floors=fl, roof="flat", doors=[(31, 1, "n"), (27, 6, "w")], ribbon=True)
    if fl == 2:
        stairs_up(d, 34, 2, "south", 2, rail=False)
    d.hut(28, 2, 2)
    counter(d, of, "s", 2, 1, [P.shelf("smooth_quartz", "potted_cactus"), P.shelf("smooth_quartz", "potted_bamboo"),
                        P.shelf("smooth_quartz", "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]"),
                        P.b("water_cauldron[level=3]")])
    counter(d, of, "e", 2, 4, [P.rack()] * min(2, need_racks(d)) + [P.b("barrel[facing=up,open=false]", "barrel[facing=up,open=false]")])
    d.set(31, 2, 4, "smooth_quartz_slab[type=top,waterlogged=false]")
    d.chair(30, 2, 4, "west", "mangrove", sit=False)
    d.set(31, 3, 4, "lantern[hanging=false,waterlogged=false]")
    floor_rug(d, of, 2, ("orange_carpet", "white_carpet"), inset=3)
    d.sign(33, 5, 0, "north", ["AGRI", "LAB"], "mangrove", glow=True, color="orange")
    for x in range(27, 36, 2):
        d.set(x, 2, 0, "moss_block")
        d.set(x, 3, 0, "fern" if x % 4 == 1 else "azalea")
    lamp_post(d, 36, 1)
    if fl == 2:
        counter(d, of, "w", 6, 1, [P.b("lectern[facing={f},has_book=true,powered=false]"), P.books(), P.books()])
        counter(d, of, "n", 6, 1, [P.shelf("smooth_quartz", "potted_fern"), P.chair("mangrove"), P.b("cartography_table"),
                            P.shelf("smooth_quartz", "potted_azalea_bush")])
        rack_bay(d, of, "w", 6, 4)
        floor_rug(d, of, 6, ("light_gray_carpet", "orange_carpet"), inset=2)
        bench(d, 22, 1, "north", 3)
        lamp_post(d, 21, 1)
    # ---- L3: hydroponic greenhouse wing ----
    if L >= 3:
        gh = bld(d, 27, 10, 37, 16, floors=1, fh=5, roof="flat", doors=[(31, 10, "n"), (27, 13, "w")], win=99,
                 wallfn=glasswall("Neoterra", "light_gray_concrete"), lamps=False)
        d.fill(28, 7, 11, 36, 7, 15, "light_blue_stained_glass")
        door_cells(d).add((31, 2, 9))
        for z in (12, 14):
            for x in range(29, 37):
                d.set(x, 1, z, "farmland[moisture=7]")
                d.set(x, 2, z, ("carrots[age=7]", "beetroots[age=3]")[x % 2])
                if x % 2:
                    d.set(x, 5, z, "end_rod[facing=down]")
        for x in range(29, 37):
            d.set(x, 2, 15, "potted_cactus" if x % 2 else "potted_bamboo")
        rack_bay(d, gh, "e", 2, 0)
    # ---- L4: research tower ----
    if L >= 4:
        rt = bld(d, 38, 1, 41, 8, floors=5, roof="flat", doors=[(38, 4, "w")], ribbon=True,
                 pal=dict(wall="white_concrete", post="orange_concrete", band="orange_terracotta", accent="orange_concrete"))
        ladder(d, 40, 7, 2, 21, "west")
        for k in range(5):
            y = 2 + 4 * k
            d.set(39, y, 2, "smooth_quartz_slab[type=top,waterlogged=false]")
            d.set(39, y + 1, 2, ("potted_cactus", "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=false]",
                                 "potted_bamboo", "lantern[hanging=false,waterlogged=false]", "potted_fern")[k])
            d.set(40, y, 2, "barrel[facing=up,open=false]" if k % 2 else "composter[level=4]")
        for x in range(28, 37, 2):
            for z in range(2, 8):
                d.set(x, 10 if fl == 2 else 6, z, "daylight_detector[inverted=false,power=0]")
        tree(d, 37, 20, 4, "azalea_leaves", "birch_log", 1)
    # ---- L5: packing hall & seed vault with a green roof, staff garden ----
    if L >= 5:
        ph = bld(d, 28, 19, 41, 30, floors=2, roof="flat", doors=[(32, 19, "n"), (28, 26, "w")], ribbon=True,
                 pal=dict(wall="white_terracotta", post="brown_terracotta", band="orange_terracotta", accent="lime_concrete",
                          deck="moss_block"))
        stairs_up(d, 40, 21, "south", 2, rail=False)
        for x in range(30, 39, 3):
            for z in (23, 24):
                d.set(x, 2, z, "smooth_quartz_slab[type=top,waterlogged=false]")
                d.set(x + 1, 2, z, "smooth_quartz_slab[type=top,waterlogged=false]")
                d.set(x, 3, z, "bamboo_block[axis=y]" if z == 23 else "potted_cactus")
        counter(d, ph, "s", 2, 1, [P.b("barrel[facing=up,open=false]", "barrel[facing=up,open=false]")] * 6)
        counter(d, ph, "s", 6, 1, [P.books()] * 6 + [P.b("lectern[facing={f},has_book=true,powered=false]")])
        counter(d, ph, "w", 6, 1, [P.b("chest[facing={f},type=single,waterlogged=false]")] * 3)
        floor_rug(d, ph, 6, ("lime_carpet", "white_carpet"), inset=3)
        for x in range(29, 41):
            for z in range(20, 30):
                if (x * 3 + z) % 4 == 0:
                    d.set(x, 11, z, ("azalea", "fern", "flowering_azalea")[x % 3])
        for x in (30, 34):
            tree(d, x, 32, 3, "azalea_leaves", "birch_log", 1)
        lamp_post(d, 37, 32)
        bench(d, 38, 33, "south", 2)
    paste_cluster(d, 0, 4)                                                   # beds 0..26 x 4..30
    return d


def plantation_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (52, 26, 44), gy=1)
    P.d = d
    d.palette = dict(wall="white_terracotta", end="white_terracotta", frame="stripped_oak_log", roof="granite",
                     shutter="bamboo", doorwood="oak", plinth="bricks", chimney="bricks")
    ps = bld(d, 11, 1, 16, 12, floors=1, axis="z", doors=[(13, 1, "n"), (13, 12, "s")])
    d.hut(12, 2, 2)
    counter(d, ps, "w", 2, 3, [P.rack()] * min(2, need_racks(d)) + [P.b("composter[level=6]")])
    counter(d, ps, "e", 2, 1, [P.shelf("oak", "flower_pot"), P.shelf("oak", "potted_cactus"), P.b("water_cauldron[level=3]"),
                        P.shelf("oak", "potted_red_tulip"), P.shelf("oak", "flower_pot"),
                        P.b("barrel[facing=up,open=false]", "white_wool")])
    floor_rug(d, ps, 2, ("green_carpet", "lime_carpet"), inset=2)
    d.sign(12, 4, 0, "north", ["Kitchen", "Garden"], "oak")
    flowerbed(d, 17, 0, 22, 0, ("poppy", "oxeye_daisy", "cornflower"))
    lamp_post(d, 10, 0)
    # ---- L2+: lean-to glasshouses along the street wall ----
    if L >= 2:
        xb = 22 if L == 2 else 28
        lean_glass(d, 16, xb, 1, 5, ends=(False, True))
        d.door(16, 2, 3, "east", "oak")
        door_cells(d).update({(15, 2, 3), (17, 2, 3)})
        rack_bay(d, ps, "w", 2, 6)
        # potting yard behind the beds: seed & tool shed, cold frames, compost bays
        sd = bld(d, 2, 35, 8, 41, floors=1, axis="x", doors=[(5, 35, "n")], chimney=None,
                 pal=dict(wall="mud_bricks", end="mud_bricks", framing=False, roof="deepslate_tile",
                          frame="stripped_dark_oak_log", shutter="dark_oak", plinth="bricks"))
        counter(d, sd, "s", 2, 0, [P.b("grindstone[face=floor,facing={f}]"), P.b("barrel[facing=up,open=false]", "white_wool"),
                            P.shelf("dark_oak", "flower_pot"), P.b("chest[facing={f},type=single,waterlogged=false]")])
        counter(d, sd, "e", 2, 1, [P.b("barrel[facing=up,open=false]", "barrel[facing=up,open=false]"), P.b("composter[level=3]")])
        for x in range(11, 27):
            if x % 4 != 2:
                d.set(x, 2, 36, "bricks" if x % 4 == 3 else "glass")
                d.set(x, 2, 37, "bricks" if x % 4 == 3 else "glass")
        for x in range(11, 20, 3):
            for dz in (39, 40, 41):
                d.set(x, 2, dz, "bricks")
            d.set(x + 1, 2, 41, "bricks")
            d.set(x + 2, 2, 41, "bricks")
            d.set(x + 1, 2, 40, "composter[level=7]")
        lamp_post(d, 10, 34)
        tree(d, 30, 39, 4)
    # ---- L3: head gardener's cottage ----
    if L >= 3:
        hc = bld(d, 31, 1, 40, 9, floors=2, axis="x", doors=[(35, 9, "s")], chimney=(40, 5),
                 pal=dict(wall="smooth_sandstone", end="smooth_sandstone", framing=False, roof="brick",
                          frame="stripped_oak_log", shutter="warped", plinth="stone_bricks"))
        stairs_up(d, 32, 7, "east", 2, rail=False)
        d.hearth(39, 2, 5, "west", 5, "bricks", "campfire")
        counter(d, hc, "n", 2, 1, [P.books(), P.books(), P.b("lectern[facing={f},has_book=true,powered=false]"), P.chair("oak")])
        d.dining(35, 2, 5, 2, "x", "oak", chairs=("n", "s"), sit=False)
        d.bed(32, 6, 2, "west")
        counter(d, hc, "n", 6, 3, [P.b("chest[facing={f},type=single,waterlogged=false]"), P.b("barrel[facing=up,open=false]"),
                            P.shelf("oak", "candle[candles=2,lit=false,waterlogged=false]")])
        floor_rug(d, hc, 2, inset=3)
        floor_rug(d, hc, 6, inset=2)
        flowerbed(d, 31, 11, 40, 12)
        rack_bay(d, hc, "e", 6, 0)
    # ---- L4: west glasshouse, bothy for the garden boys ----
    if L >= 4:
        lean_glass(d, 2, 11, 1, 5, ends=(True, False))
        d.door(11, 2, 3, "west", "oak")
        door_cells(d).update({(10, 2, 3), (12, 2, 3)})
        bo = bld(d, 31, 14, 40, 21, floors=1, axis="x", doors=[(35, 14, "n")], chimney=(31, 17),
                 pal=dict(wall="bricks", end="bricks", framing=False, roof="mud_brick", frame="stripped_spruce_log",
                          shutter="spruce", plinth="stone_bricks"))
        d.hearth(32, 2, 17, "east", 5, "bricks", "campfire")
        for x in (34, 36, 38):
            d.bed(x, 2, 20, "south")
        counter(d, bo, "e", 2, 0, [P.b("chest[facing={f},type=single,waterlogged=false]"), P.b("barrel[facing=up,open=false]")])
        tree(d, 42, 12, 4)
        # vinery: long lean-to glasshouse along the south wall
        vn = bld(d, 21, 38, 43, 42, floors=1, fh=5, axis="x", doors=[(32, 38, "n")], win=99, lamps=False,
                 wallfn=lambda x, y, z, rel, c, a, k: "bricks" if c or y == 2 or rel == 4 or z == 42 or x % 4 == 1 else "glass",
                 pal=dict(roof="granite", end="bricks"))
        for x in range(23, 42):
            d.set(x, 1, 41, "grass_block[snowy=false]")
            d.set(x, 2, 41, leaves("oak_leaves") if x % 3 else "sweet_berry_bush[age=3]")
        counter(d, vn, "n", 2, 2, [P.b("water_cauldron[level=3]"), P.shelf("oak", "flower_pot")] * 3)        # walled orchard path with espaliers and a sundial
        for x in range(30, 46):
            if x not in (35, 36):
                d.set(x, 2, 22, "bricks")
                d.set(x, 3, 22, "brick_slab[type=bottom,waterlogged=false]")
        for z in range(10, 22):
            d.set(45, 2, z, "bricks")
            d.set(45, 3, z, "brick_slab[type=bottom,waterlogged=false]")
            if z % 3 == 0:
                d.set(44, 2, z, leaves("oak_leaves"))
        d.set(42, 2, 17, "chiseled_stone_bricks")
        d.set(42, 3, 17, "stone_brick_slab[type=bottom,waterlogged=false]")
    # ---- L5: orangery (classical glass pavilion) ----
    if L >= 5:
        og = bld(d, 30, 23, 43, 33, floors=1, fh=6, roof="hip", doors=[(36, 23, "n")], win=99, lamps=False,
                 wallfn=lambda x, y, z, rel, c, a, k: "smooth_sandstone" if c or y == 2 or rel == 5 or
                 (x if a == "x" else z) % 3 == 0 else "glass",
                 pal=dict(roof="granite"))
        for x in range(32, 42, 3):
            for z in (25, 31):
                d.set(x, 1, z, "grass_block[snowy=false]")
                tree(d, x, z, 3, "azalea_leaves", "oak_log", 1)
        for x in range(32, 42):
            d.set(x, 1, 28, "smooth_sandstone")
        for x in (33, 39):
            bench(d, x, 27, "north", 2)
        d.set(36, 2, 28, "water_cauldron[level=3]")
        for x in (29, 44):
            lamp_post(d, x, 23)
        # fountain and topiary on the orangery forecourt
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                d.set(36 + dx, 2, 20 + dz, "smooth_sandstone_slab[type=bottom,waterlogged=false]" if (dx, dz) != (0, 0) else "water")
        d.set(36, 1, 20, "water")
        for x in (32, 40):
            d.set(x, 2, 20, leaves("oak_leaves"))
            d.set(x, 3, 20, leaves("oak_leaves"))
        for x in range(30, 44, 2):
            d.set(x, 2, 34, "potted_red_tulip" if x % 4 else "potted_orange_tulip")
        # apple store & fruit room
        ap = bld(d, 46, 1, 51, 12, floors=2, axis="z", doors=[(46, 6, "w")], chimney=None,
                 pal=dict(wall="calcite", end="calcite", roof="deepslate_tile", frame="stripped_dark_oak_log",
                          shutter="crimson", plinth="stone_bricks"))
        stairs_up(d, 50, 2, "south", 2, rail=False)
        for z in range(2, 12):
            for x in (47, 48):
                if z != 6:
                    d.set(x, 2, z, "spruce_slab[type=top,waterlogged=false]" if x == 47 else "barrel[facing=up,open=false]")
        for z in range(7, 12):
            d.set(47, 3, z, "red_wool" if z % 2 else "lime_wool")
        counter(d, ap, "w", 6, 1, [P.b("barrel[facing=up,open=false]", "barrel[facing=up,open=false]")] * 4)
        floor_rug(d, ap, 6, inset=2)
        for x, z in ((48, 16), (48, 22), (48, 28), (48, 34), (48, 40)):
            tree(d, x, z, 4)
    paste_cluster(d, 2, 6)                                                   # beds 2..28 x 6..32
    return d


def plantation_cascadia(rel, L):
    d = Design("Cascadia", rel, (54, 26, 34), gy=1, paving="coarse_dirt")
    P.d = d
    d.palette = dict(wall="dark_oak_log", siding="dark_oak_planks", batten="stripped_dark_oak_log", end="dark_oak_planks",
                     trim="yellow_terracotta", roof="mangrove", shutter="bamboo", doorwood="dark_oak", plinth="tuff")
    fs = bld(d, 22, 2, 31, 9, floors=1, axis="z", doors=[(26, 2, "n")])
    d.hut(23, 2, 3)
    counter(d, fs, "e", 2, 0, [P.rack()] * min(2, need_racks(d)) + [P.b("bamboo_block[axis=y]", "bamboo_block[axis=y]"),
                        P.b("barrel[facing=up,open=false]", "brown_wool")])
    counter(d, fs, "s", 2, 1, [P.b("bamboo_block[axis=x]")] * 3 + [P.shelf("dark_oak", "potted_cactus")])
    floor_rug(d, fs, 2, ("yellow_carpet", "brown_carpet"), inset=2)
    # farm stand on the street
    for x in range(22, 32):
        d.set(x, 5, 0, "yellow_terracotta" if x % 2 else "dark_oak_slab[type=bottom,waterlogged=false]")
    posts(d, [(22, 0), (31, 0)], 2, 4, "dark_oak_fence")
    for x, b in ((23, "melon"), (24, "pumpkin"), (29, "hay_block[axis=y]"), (30, "melon")):
        d.set(x, 2, 0, b)
    d.set(25, 2, 0, "barrel[facing=up,open=false]")
    d.sign(27, 4, 1, "north", ["CEDAR CREEK", "FARM STAND"], "dark_oak")
    lamp_post(d, 33, 1)
    if L >= 2:                                                        # cane press lean-to
        lp = bld(d, 32, 3, 37, 9, floors=1, axis="x", doors=[(34, 3, "n")],
                 pal=dict(wall="spruce_planks", siding="spruce_planks", batten="stripped_spruce_log", roof="spruce"))
        d.set(34, 2, 5, "grindstone[face=floor,facing=north]")
        d.set(35, 2, 5, "water_cauldron[level=3]")
        d.set(36, 2, 5, "composter[level=4]")
        for z in (7, 8):
            d.set(36, 2, z, "barrel[facing=up,open=false]")
        rack_bay(d, lp, "s", 2, 2)
        woodpile(d, 38, 5, 3, "z")
        for x in range(33, 37):                                       # cane bundles drying on racks
            d.set(x, 2, 11, "spruce_fence")
            d.set(x, 3, 11, "bamboo_block[axis=x]" if x % 2 else "spruce_fence")
        cart(d, 35, 1, "x", "melon")
        lamp_post(d, 39, 9)
        bench(d, 28, 1, "north", 2)
        flowerbed(d, 39, 11, 44, 11, ("dandelion", "poppy", "cornflower"))
    if L >= 3:                                                        # gambrel barn replacing the shed's back
        bn = bld(d, 22, 11, 31, 22, floors=1, fh=6, roof="gambrel", axis="z", doors=[(26, 11, "n")], win=4,
                 pal=dict(roof="deepslate_tile"))
        for x in (25, 27):
            for y in (2, 3, 4):
                d.set(x, y, 11, AIR)
        door_cells(d).update({(25, 2, 12), (27, 2, 12), (25, 2, 10), (27, 2, 10)})
        counter(d, bn, "w", 2, 2, [P.b("bamboo_block[axis=y]", "bamboo_block[axis=y]")] * 5)
        counter(d, bn, "e", 2, 2, [P.b("hay_block[axis=y]", "hay_block[axis=z]")] * 4)
        rack_bay(d, bn, "s", 2, 0)
        cart(d, 26, 17, "z", "melon")
    if L >= 4:                                                        # sugar mill with a water wheel
        sm = bld(d, 34, 12, 43, 21, floors=2, fh=5, axis="z", doors=[(38, 12, "n")], chimney=(43, 16),
                 pal=dict(wall="stripped_spruce_log", siding="mangrove_planks", batten="stripped_spruce_log",
                          end="mangrove_planks", roof="spruce", shutter="spruce", plinth="cobblestone"))
        stairs_up(d, 35, 20, "north", 2, fh=5, rail=False)
        for z in (14, 16, 18):
            d.set(38, 2, z, "grindstone[face=floor,facing=north]")
            d.set(40, 2, z, "water_cauldron[level=3]")
        d.set(42, 2, 16, "blast_furnace[facing=west,lit=true]")
        counter(d, sm, "e", 7, 1, [P.b("barrel[facing=up,open=false]", "barrel[facing=up,open=false]")] * 4)
        for dy in range(-3, 4):                                       # water wheel on the west wall
            for dz in range(-3, 4):
                if 2 <= abs(dy) + abs(dz) <= 4 and (abs(dy) == 3 or abs(dz) == 3 or dy == 0 or dz == 0):
                    y, z = 7 + dy, 16 + dz
                    if y >= 2:
                        d.set(33, y, z, "stripped_spruce_log[axis=x]" if dy == 0 or dz == 0 else "spruce_planks")
        d.set(33, 7, 16, "spruce_log[axis=x]")
        for z in range(13, 20):
            d.set(32, 1, z, "water")
    if L >= 5:                                                        # water tower and cutters' cabins
        tx, tz = 40, 1
        posts(d, [(tx, tz), (tx + 3, tz), (tx, tz + 3), (tx + 3, tz + 3)], 2, 9, "spruce_log[axis=y]")
        for x in range(tx, tx + 4):
            for z in range(tz, tz + 4):
                d.set(x, 10, z, "spruce_planks")
                for y in (11, 12, 13):
                    if x in (tx, tx + 3) or z in (tz, tz + 3):
                        d.set(x, y, z, "stripped_spruce_log[axis=y]" if y != 12 else "spruce_planks")
                    else:
                        d.set(x, y, z, "water")
        d.hip(tx, tz, tx + 3, tz + 3, 14, "dark_oak_stairs", "dark_oak_slab", overhang=0)
        for i, x0 in enumerate((30, 37)):
            cb = bld(d, x0, 26, x0 + 6, 32, floors=1, axis="x", doors=[(x0 + 3, 26, "n")], chimney=(x0 + 6, 29),
                     pal=dict(wall="spruce_log", siding="birch_planks", batten="stripped_spruce_log",
                              roof=("mangrove", "deepslate_tile")[i], shutter=("bamboo", "mangrove")[i]))
            d.bed(x0 + 1, 2, 31, "south")
            d.bed(x0 + 3, 2, 31, "south")
            d.set(x0 + 5, 2, 29, "campfire[facing=west,lit=true,signal_fire=false,waterlogged=false]")
            counter(d, cb, "n", 2, 0, [P.b("chest[facing={f},type=single,waterlogged=false]")])
            porch(d, x0, x0 + 6, 26, 2, "n", gaps=(x0 + 3,))
        for x, z in ((44, 25), (44, 32), (29, 33)):
            tree(d, x, z, 6, "spruce_leaves", "spruce_log", 2)
        mh = bld(d, 46, 13, 52, 21, floors=2, axis="z", doors=[(49, 13, "n")], chimney=(52, 17),
                 pal=dict(wall="spruce_log", siding="dark_oak_planks", batten="stripped_dark_oak_log",
                          roof="dark_prismarine", shutter="mangrove", plinth="cobblestone"))
        d.hearth(51, 2, 17, "west", 5, "cobblestone", "campfire")
        stairs_up(d, 47, 15, "south", 2, rail=False)
        d.dining(49, 2, 16, 3, "z", "spruce", chairs=("e", "w"), sit=False)
        counter(d, mh, "n", 6, 1, [P.b("barrel[facing=up,open=false]")] * 3 + [P.b("chest[facing={f},type=single,waterlogged=false]")])
        d.bed(51, 6, 20, "south")
        porch(d, 46, 52, 13, 2, "n", gaps=(49,))
    paste_cluster(d, 0, 6)                                                   # beds 0..26 x 6..32
    return d


@design("plantation")
def plantation(pack, rel, L):
    return {"Hearthwood": plantation_hearthwood, "Cascadia": plantation_cascadia,
            "Neoterra": plantation_neoterra}[pack](rel, L)


# ================================================================================================== FARMER
def compost_bay(d, x, y, z, along="x"):
    """Three composters side by side (the hut's work blocks)."""
    dx, dz = (1, 0) if along == "x" else (0, 1)
    for i in range(3):
        d.item(x + dx * i, y, z + dz * i, "composter")


def veg_rows(d, x1, z1, x2, z2, crops=("wheat[age=7]", "carrots[age=7]", "potatoes[age=7]", "beetroots[age=3]"),
             water_col=None):
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if water_col is not None and x == water_col:
                d.set(x, 1, z, "water")
                continue
            d.set(x, 1, z, "farmland[moisture=7]")
            d.set(x, 2, z, crops[(z - z1) % len(crops)])


def farmer_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (40, 26, 36), gy=1)
    P.d = d
    d.palette = dict(wall="smooth_sandstone", end="smooth_sandstone", framing=False, frame="stripped_oak_log",
                     roof="brick", shutter="warped", doorwood="oak", plinth="stone_bricks", chimney="bricks")
    W = "dark_oak"
    # ---- farmhouse (L1 one storey, L2+ two) ----
    fl = 1 if L == 1 else 2
    fh_ = bld(d, 3, 4, 11, 10, floors=fl, axis="x", doors=[(7, 4, "n"), (5, 10, "s")], chimney=(11, 7))
    d.hut(4, 2, 5)
    d.hearth(10, 2, 7, "west", 5, "bricks", "campfire")
    d.set(10, 3, 7, "bricks")
    d.set(10, 4, 7, "bricks")
    if fl == 2:
        stairs_up(d, 6, 9, "east", 2, rail=False)
    # farm kitchen: work wall on the north side, racks by the back door, fireside chairs, table in the middle
    d.item(5, 2, 5, "crafting_table")
    rm = Rm(d, fh_, 2, "n", "oak")
    rm.put(2, 0, SLAB)
    rm.put(2, 0, POT, 1)
    rm.put(4, 0, "smoker[facing=south,lit=true]")
    rm.put(5, 0, "water_cauldron[level=3]")
    rm.put(6, 0, SLAB)
    rm.put(6, 0, CANDLE, 1)
    d.rack(4, 2, 7, "east")
    d.rack(4, 2, 8, "east")
    rm.chair(5, 1, "west")
    rm.chair(5, 3, "west")
    rm.put(2, 2, "oak_fence")
    rm.put(2, 2, "oak_pressure_plate[powered=false]", 1)
    rm.chair(1, 2, "west")
    rm.chair(3, 2, "east")
    rm.rug(1, 1, 3, 3, ("red_carpet",))
    if fl == 2:
        # bedroom above: bed against the north wall, nightstand, wardrobe, writing desk at the window
        up = Rm(d, fh_, 6, "n", "dark_oak")
        up.bed(1, 0)
        up.put(0, 0, SLAB)
        up.put(0, 0, "candle[candles=2,lit=false,waterlogged=false]", 1)
        up.put(2, 0, SLAB)
        up.put(2, 0, "potted_red_tulip", 1)
        up.put(0, 3, BARREL)
        up.put(0, 3, BARREL, 1)
        up.put(0, 2, CHEST)
        up.put(4, 0, BOOKS)
        up.put(5, 0, SLAB)
        up.put(-2, 2, LECTERN)
        up.chair(5, 1, "in")
        up.put(6, 1, "loom[facing=west]")
        up.rug(1, 2, 4, 3, ("red_carpet", "orange_carpet"))
    d.sign(8, 4, 3, "north", ["Meadowbrook", "Farm"], W)
    # ---- yard: compost bay, kitchen garden, path ----
    compost_bay(d, 3, 2, 13)
    fence_line(d, [(2, 12), (2, 13), (2, 14), (3, 14), (4, 14), (5, 14), (6, 14), (6, 12), (6, 13)])
    veg_rows(d, 8, 13, 11, 16, water_col=None)
    fence_line(d, [(x, 17) for x in range(7, 13)] + [(7, z) for z in range(12, 17)] + [(12, z) for z in range(12, 17)],
               gate=(9, 17, "south"))
    path(d, [(7, z) for z in range(0, 4)])
    lamp_post(d, 9, 2)
    bench(d, 4, 2, "north", 2)
    tree(d, 1, 2, 4)
    # ---- L2: tool shed ----
    if L >= 2:
        ts = bld(d, 14, 4, 18, 8, floors=1, axis="z", doors=[(16, 4, "n")],
                 pal=dict(wall="dark_oak_planks", end="dark_oak_planks", roof="deepslate_tile", frame="dark_oak_log",
                          shutter="dark_oak"))
        # tool shed: rack bay on the back wall, sharpening corner, seed barrels by the door
        rm = Rm(d, ts, 2, "s", "dark_oak")
        for u in range(min(3, need_racks(d))):
            rm.rack(u, 0)
        rm.put(0, 1, "grindstone[face=floor,facing=east]")
        rm.put(2, 1, "anvil[facing=north]")
        rm.put(0, 2, BARREL)
        rm.put(0, 2, "white_wool", 1)
        rm.put(2, 2, CHEST.replace("{in}", "west"))
        woodpile(d, 14, 10, 4)
        cart(d, 21, 5, "z")
    # ---- L3: threshing barn ----
    if L >= 3:
        bn = bld(d, 14, 14, 24, 26, floors=1, fh=6, axis="z", doors=[(19, 14, "n")], win=4,
                 pal=dict(wall="dark_oak_planks", end="dark_oak_planks", framing=True, frame="stripped_dark_oak_log",
                          roof="deepslate_tile", plinth="cobblestone", shutter="dark_oak"))
        for x in (18, 20):
            for y in (2, 3, 4):
                d.set(x, y, 14, AIR)
        door_cells(d).update({(18, 2, 15), (20, 2, 15), (18, 2, 13), (20, 2, 13)})
        # threshing barn: grain barrels on the east bay, hay mows west and south, threshing floor with the wain
        for z in range(16, 20):
            d.item(23, 2, z, "barrel")
        rm = Rm(d, bn, 2, "w", "dark_oak")
        for u in range(1, 9):
            rm.put(u, 0, "hay_block[axis=z]")
            rm.put(u, 0, "hay_block[axis=y]", 1)
            if u % 2:
                rm.put(u, 1, "hay_block[axis=z]")
        sm = Rm(d, bn, 2, "s", "dark_oak")
        for u in range(need_racks(d)):
            sm.rack(u, 0)
        for u in range(3, 8):
            sm.put(u, 0, "hay_block[axis=x]")
        cart(d, 20, 21, "z", "hay_block[axis=y]")
        d.set(23, 2, 21, "grindstone[face=floor,facing=west]")
        d.set(23, 2, 22, "composter[level=3]")
        fence_line(d, [(x, 13) for x in (15, 16)])
        hay_rick(d, 26, 15)
    # ---- L4: stable & cart shed range, paddock ----
    if L >= 4:
        st_ = bld(d, 26, 19, 34, 27, floors=2, axis="x", doors=[(30, 19, "n")], chimney=None,
                  pal=dict(wall="bricks", end="bricks", roof="mud_brick", frame="stripped_spruce_log", shutter="spruce"))
        for x in range(27, 34):                                       # hay loft over the stalls
            for z in range(20, 27):
                if (x + z) % 3 == 0 and z > 21:
                    d.set(x, 6, z, "hay_block[axis=y]")
        ladder(d, 33, 20, 2, 5, "west")
        d.set(33, 5, 20, "ladder[facing=west,waterlogged=false]")
        for x in range(27, 34):
            if x % 3 == 0:
                for z in range(23, 27):
                    d.set(x, 2, z, "dark_oak_fence")
        for x in range(28, 34, 3):
            d.set(x, 2, 26, "hay_block[axis=y]")
            d.set(x, 2, 25, "water_cauldron[level=3]")
        # tack room corner by the door
        d.set(27, 2, 20, BARREL)
        d.set(28, 2, 20, "dark_oak_slab[type=top,waterlogged=false]")
        d.set(28, 3, 20, LANT)
        d.set(29, 2, 20, "chest[facing=south,type=single,waterlogged=false]")
        fence_line(d, [(x, 33) for x in range(26, 39)] + [(26, z) for z in range(29, 33)] +
                   [(38, z) for z in range(20, 33)], gate=(30, 33, "south"))
        hay_rick(d, 35, 30)
        tree(d, 37, 16, 5)
        lamp_post(d, 25, 18)
        bench(d, 22, 28, "south", 2)
        flowerbed(d, 3, 19, 11, 21)
        bench(d, 6, 23, "south", 3)
    # ---- L5: dovecote, granary on staddles, orchard, well ----
    if L >= 5:
        dc = bld(d, 28, 4, 32, 8, floors=3, axis="x", roof="hip", doors=[(30, 8, "s")], win=2,
                 pal=dict(roof="deepslate_tile", wall="smooth_sandstone"))
        for x in range(29, 32):
            d.set(x, 11, 4, "dark_oak_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]")
        d.set(30, 2, 5, "hay_block[axis=y]")
        gr = 22
        for x in (gr, gr + 4):
            for z in (4, 8):
                d.set(x, 2, z, "mossy_cobblestone")
        g2 = bld(d, gr, 4, gr + 4, 8, floors=1, axis="x", doors=[(gr + 2, 8, "s")], win=9,
                 pal=dict(wall="oak_planks", end="oak_planks", framing=True, frame="stripped_dark_oak_log", roof="spruce"))
        well(d, 34, 11)
        # farmworkers' cottage with kitchen and bunk room
        ck = bld(d, 2, 25, 10, 32, floors=2, axis="z", doors=[(6, 25, "n")], chimney=(2, 29),
                 pal=dict(wall="yellow_terracotta", end="yellow_terracotta", framing=True, frame="stripped_dark_oak_log",
                          roof="deepslate_tile", shutter="crimson"))
        d.hearth(3, 2, 29, "east", 5, "bricks", "campfire")
        stairs_up(d, 9, 27, "south", 2, rail=False)
        lay_kitchen(Rm(d, ck, 2, "n", "oak"))
        lay_bunks(Rm(d, ck, 6, "w", "dark_oak"), 3)
        for x, z in ((14, 30), (18, 33), (22, 30), (26, 33), (30, 30), (34, 33)):
            tree(d, x, z, 4, "oak_leaves")
        for x in range(12, 39):
            d.set(x, 2, 35, "dark_oak_fence")
    return d


def farmer_cascadia(rel, L):
    d = Design("Cascadia", rel, (46, 28, 40), gy=1, paving="coarse_dirt")
    P.d = d
    d.palette = dict(shutter="mangrove", doorwood="spruce", plinth="mossy_cobblestone", trim="stripped_spruce_log")
    W = "spruce"
    # ---- log cabin with porch (L2+ sleeping loft storey) ----
    fl = 1 if L == 1 else 2
    cb = bld(d, 3, 6, 11, 13, floors=fl, axis="z", doors=[(7, 6, "n"), (9, 13, "s")], chimney=(3, 10))
    porch(d, 3, 11, 6, 3, "n", gaps=(7,))
    d.hut(10, 2, 7)
    d.hearth(4, 2, 10, "east", 5, "cobblestone", "campfire")
    counter(d, cb, "e", 2, 1, [P.item("crafting_table"), P.rack(), P.rack(), P.b("barrel[facing=up,open=false]", "brown_wool")])
    counter(d, cb, "s", 2, 2, [P.b("smoker[facing={f},lit=true]"), P.shelf("spruce", "decorated_pot[cracked=false,facing=north,waterlogged=false]"),
                        P.b("water_cauldron[level=3]")])
    counter(d, cb, "n", 2, 0, [P.books(), P.shelf("spruce", "lantern[hanging=false,waterlogged=false]")])
    d.dining(7, 2, 9, 2, "z", "spruce", chairs=("e", "w"), sit=False)
    floor_rug(d, cb, 2, inset=3)
    d.sign(9, 4, 5, "north", ["Elk Ridge", "Homestead"], W)
    if fl == 2:
        stairs_up(d, 5, 12, "north", 2, rail=False)
        d.bed(4, 6, 8, "west")
        counter(d, cb, "e", 6, 0, [P.b("chest[facing={f},type=single,waterlogged=false]"), P.b("barrel[facing=up,open=false]"),
                            P.shelf("spruce", "candle[candles=2,lit=false,waterlogged=false]"), P.b("loom[facing={f}]")])
        floor_rug(d, cb, 6, inset=2)
    # ---- yard ----
    compost_bay(d, 13, 2, 7, "z")
    fence_line(d, [(14, z) for z in range(6, 11)] + [(13, 6), (13, 10)])
    veg_rows(d, 3, 17, 11, 21, water_col=7)
    fence_line(d, [(x, 16) for x in range(2, 13) if x != 9] + [(x, 22) for x in range(2, 13)] +
               [(2, z) for z in range(17, 22)] + [(12, z) for z in range(17, 22)], gate=(9, 16, "north"))
    woodpile(d, 12, 12, 3, "z")
    d.set(13, 2, 13, "spruce_log[axis=y]")                            # chopping block
    d.set(13, 3, 13, "spruce_slab[type=bottom,waterlogged=false]")
    lamp_post(d, 6, 1)
    tree(d, 1, 3, 6, "spruce_leaves", "spruce_log", 2)
    # ---- L2: tool lean-to & woodshed ----
    if L >= 2:
        ts = bld(d, 15, 4, 20, 9, floors=1, axis="x", doors=[(17, 4, "n")],
                 pal=dict(wall="birch_planks", siding="birch_planks", end="birch_planks", roof="mangrove", shutter="spruce"))
        counter(d, ts, "s", 2, 0, [P.b("grindstone[face=floor,facing={f}]")] + [P.rack()] * min(3, need_racks(d)) +
            [P.b("anvil[facing=east]")])
        counter(d, ts, "e", 2, 0, [P.b("barrel[facing=up,open=false]", "barrel[facing=up,open=false]"),
                            P.b("chest[facing={f},type=single,waterlogged=false]")])
        counter(d, ts, "w", 2, 0, [P.shelf("spruce", "lantern[hanging=false,waterlogged=false]")])
        cart(d, 22, 6, "z", "pumpkin")
    # ---- L3: gambrel barn ----
    if L >= 3:
        bn = bld(d, 16, 13, 26, 27, floors=1, fh=6, roof="gambrel", axis="z", doors=[(21, 13, "n")], win=4,
                 pal=dict(wall="mangrove_planks", siding="mangrove_planks", batten="stripped_birch_log",
                          end="mangrove_planks", trim="white_terracotta", roof="deepslate_tile", shutter="birch",
                          plinth="cobblestone"))
        for x in (20, 22):
            for y in (2, 3, 4):
                d.set(x, y, 13, AIR)
        door_cells(d).update({(20, 2, 14), (22, 2, 14), (20, 2, 12), (22, 2, 12)})
        for x in (19, 23):                                           # X-braced door leaves
            for y in (2, 3, 4):
                d.set(x, y, 12, trap("spruce", "north", "bottom", True))
        for z in range(15, 19):
            d.item(17, 2, z, "barrel")
        rack_bay(d, bn, "e", 2, 1)
        counter(d, bn, "e", 2, 1, [P.b("hay_block[axis=y]", "hay_block[axis=z]")] * 4)
        counter(d, bn, "s", 2, 0, [P.b("water_cauldron[level=3]"), P.b("hay_block[axis=x]"), P.b("composter[level=5]")])
        for z in range(20, 26):                                       # stalls
            if z % 3 == 2:
                for x in (17, 18, 19):
                    d.set(x, 2, z, "spruce_fence")
        cart(d, 21, 19, "z", "hay_block[axis=y]")
        hay_rick(d, 28, 14)
    # ---- L4: corral, chicken coop, stable lean-to ----
    if L >= 4:
        fence_line(d, [(x, 29) for x in range(28, 45)] + [(x, 38) for x in range(28, 45)] +
                   [(28, z) for z in range(30, 38)] + [(44, z) for z in range(30, 38)], gate=(32, 29, "north"))
        d.set(40, 2, 31, "water_cauldron[level=3]")
        d.set(41, 2, 31, "hay_block[axis=y]")
        hay_rick(d, 38, 35)
        co = bld(d, 30, 4, 36, 9, floors=1, axis="x", doors=[(33, 9, "s")], win=3,
                 pal=dict(wall="birch_planks", siding="birch_planks", end="birch_planks", roof="mangrove",
                          trim="yellow_terracotta", shutter="bamboo"))
        for x in range(31, 36):
            d.set(x, 2, 5, "hay_block[axis=y]" if x % 2 else "spruce_slab[type=top,waterlogged=false]")
            d.set(x, 3, 5, "spruce_trapdoor[facing=south,half=bottom,open=false,powered=false,waterlogged=false]")
        counter(d, co, "s", 2, 0, [P.b("composter[level=2]"), P.b("barrel[facing=up,open=false]")])
        fence_line(d, [(x, 11) for x in range(30, 37) if x != 34] + [(30, 10), (36, 10)])
        # machine shed: open-fronted pole barn with the seed drill and wagons
        for x in (38, 41, 44):
            for z in (3, 11):
                posts(d, [(x, z)], 2, 5, "spruce_log[axis=y]")
        for z in range(3, 12):
            d.set(44, 2, z, "spruce_planks")
            d.set(44, 3, z, "spruce_planks")
            d.set(44, 4, z, "spruce_planks")
        d.gable(38, 3, 44, 11, 6, "z", "spruce_stairs", "spruce_slab", "spruce_planks", overhang=1)
        for x in range(39, 44):
            d.set(x, 5, 11, "spruce_planks")
            d.set(x, 4, 11, "spruce_planks")
        cart(d, 40, 5, "z", "hay_block[axis=y]")
        cart(d, 42, 8, "z", "melon")
        d.set(43, 2, 4, "grindstone[face=floor,facing=west]")
        d.set(43, 2, 10, "anvil[facing=north]")
        st_ = bld(d, 28, 15, 34, 25, floors=2, axis="z", doors=[(28, 20, "w")])
        for x in range(29, 34):
            for z in range(16, 25):
                if (x * 2 + z) % 3 == 0:
                    d.set(x, 6, z, "hay_block[axis=y]")
        ladder(d, 29, 24, 2, 5, "east")
        d.set(29, 5, 24, "ladder[facing=east,waterlogged=false]")
        for z in range(16, 25, 3):
            for x in (31, 32, 33):
                d.set(x, 2, z, "spruce_fence")
        for z in range(17, 25, 3):
            d.set(33, 2, z, "hay_block[axis=y]")
            d.set(32, 2, z, "water_cauldron[level=3]")
    # ---- L5: stave silo, water-pump windmill, bunkhouse ----
    if L >= 5:
        sx, sz = 27, 7
        ring = [(1, 0), (2, 0), (0, 1), (3, 1), (0, 2), (3, 2), (1, 3), (2, 3)]
        for y in range(1, 16):
            for dx, dz in ring:
                d.set(sx + dx, y, sz + dz, "cobblestone" if y <= 2 else
                      ("stripped_dark_oak_log[axis=y]" if y % 4 == 0 else "spruce_planks"))
            for dx in (1, 2):
                for dz in (1, 2):
                    d.set(sx + dx, y, sz + dz, "hay_block[axis=y]" if y < 14 else AIR)
        for dx, dz, f in ((1, 0, "south"), (2, 0, "south"), (0, 1, "east"), (3, 1, "west"), (0, 2, "east"),
                          (3, 2, "west"), (1, 3, "north"), (2, 3, "north")):
            d.set(sx + dx, 16, sz + dz, stair("dark_oak", f))
        for dx in (1, 2):
            for dz in (1, 2):
                d.set(sx + dx, 16, sz + dz, "dark_oak_planks")
                d.set(sx + dx, 17, sz + dz, slab("dark_oak"))
        # windmill: lattice tower with a vaned wheel
        wx, wz = 40, 15
        for y in range(2, 14):
            for dx, dz in ((0, 0), (2, 0), (0, 2), (2, 2)):
                d.set(wx + dx, y, wz + dz, "spruce_fence" if y % 4 else "stripped_spruce_log[axis=y]")
        d.fill(wx, 14, wz, wx + 2, 14, wz + 2, "spruce_planks")
        d.set(wx + 1, 15, wz + 1, "spruce_fence")
        d.set(wx + 1, 16, wz + 1, "spruce_planks")
        for k in range(1, 4):
            for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
                d.set(wx + 1 + dx, 16 + dy, wz, "white_wool" if k > 1 else "spruce_planks")
        d.set(wx + 1, 16, wz + 2, "spruce_fence")
        d.set(wx + 1, 16, wz + 3, "spruce_planks")
        d.set(wx + 1, 2, wz + 1, "water_cauldron[level=3]")
        bk = bld(d, 36, 22, 44, 27, floors=2, axis="x", doors=[(40, 22, "n")], chimney=(44, 24),
                 pal=dict(roof="dark_prismarine", shutter="spruce"))
        stairs_up(d, 42, 26, "west", 2, rail=False)
        for x in (37, 39, 41, 43):
            d.bed(x, 6, 23, "north")
        counter(d, bk, "s", 6, 0, [P.b("chest[facing={f},type=single,waterlogged=false]"), P.b("barrel[facing=up,open=false]")])
        floor_rug(d, bk, 6, inset=2)
        # smokehouse & creamery
        cr = bld(d, 2, 27, 12, 34, floors=2, axis="x", doors=[(7, 27, "n")], chimney=(2, 30),
                 pal=dict(wall="birch_planks", siding="birch_planks", end="birch_planks", roof="deepslate_tile",
                          trim="green_terracotta", shutter="warped"))
        d.hearth(3, 2, 30, "east", 5, "cobblestone", "campfire")
        counter(d, cr, "s", 2, 4, [P.b("water_cauldron[level=3]"), P.b("barrel[facing=up,open=false]", "white_wool"),
                            P.b("smoker[facing={f},lit=true]"), P.shelf("spruce", "decorated_pot[cracked=false,facing=north,waterlogged=false]"),
                            P.b("barrel[facing=up,open=false]", "barrel[facing=up,open=false]")])
        counter(d, cr, "e", 2, 0, [P.shelf("spruce", "cake[bites=0]"), P.b("chest[facing={f},type=single,waterlogged=false]")])
        stairs_up(d, 11, 32, "west", 2, rail=False)
        for x in range(3, 12):
            for z in (28, 29):
                if x % 2:
                    d.set(x, 9, z, CHAIN)
                    d.set(x, 8, z, "brown_wool")
        counter(d, cr, "n", 6, 5, [P.b("barrel[facing=up,open=false]", "barrel[facing=up,open=false]")] * 3)
        for x in (37, 39, 41):
            d.bed(x, 2, 26, "south")
        counter(d, bk, "n", 2, 0, [P.b("chest[facing={f},type=single,waterlogged=false]"), P.b("barrel[facing=up,open=false]")])
        d.set(43, 2, 24, "campfire[facing=west,lit=true,signal_fire=false,waterlogged=false]")
        porch(d, 36, 44, 22, 2, "n", gaps=(40,))
        for x, z in ((14, 30), (14, 36), (6, 37), (19, 36), (24, 36), (24, 30)):
            tree(d, x, z, 6, "spruce_leaves", "spruce_log", 2)
    return d


def farmer_neoterra(rel, L):
    d = Design("Neoterra", rel, (44, 24, 40), gy=1, paving="smooth_stone")
    P.d = d
    d.palette = dict(wall="white_concrete", post="birch_planks", band="lime_terracotta", accent="lime_concrete",
                     deck="moss_block", doorwood="birch", plinth="polished_andesite")
    # ---- office / farm kitchen (L2+ two storeys with an upstairs lab) ----
    fl = 1 if L == 1 else 2
    of = bld(d, 2, 3, 10, 10, floors=fl, roof="flat", doors=[(6, 3, "n"), (10, 7, "e")], ribbon=True)
    d.hut(3, 2, 4)
    counter(d, of, "s", 2, 0, [P.item("crafting_table"), P.shelf("smooth_quartz", "potted_bamboo"), P.b("water_cauldron[level=3]"),
                        P.shelf("smooth_quartz", "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=false]")])
    counter(d, of, "w", 2, 2, [P.rack(), P.rack(), P.b("barrel[facing=up,open=false]")])
    d.set(6, 2, 7, "smooth_quartz_slab[type=top,waterlogged=false]")
    d.chair(5, 2, 7, "west", "birch", sit=False)
    d.chair(7, 2, 7, "east", "birch", sit=False)
    d.set(6, 3, 7, "potted_azalea_bush")
    floor_rug(d, of, 2, ("lime_carpet", "white_carpet"), inset=3)
    d.sign(4, 4, 2, "north", ["AGRI", "HUB"], "birch", glow=True, color="lime")
    if fl == 2:
        stairs_up(d, 4, 9, "east", 2, rail=False)
        counter(d, of, "n", 6, 0, [P.shelf("smooth_quartz", "potted_fern"), P.shelf("smooth_quartz", "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]"),
                            P.b("lectern[facing={f},has_book=true,powered=false]"), P.books(), P.shelf("smooth_quartz", "potted_cactus")])
        counter(d, of, "w", 6, 0, [P.chair("birch"), P.b("smooth_quartz_slab[type=top,waterlogged=false]", "lantern[hanging=false,waterlogged=false]")])
        floor_rug(d, of, 6, ("light_gray_carpet", "lime_carpet"), inset=2)
        for x in range(3, 10, 3):
            d.set(x, 11, 5, "daylight_detector[inverted=false,power=0]")
    # ---- compost station under a canopy, raised beds ----
    for z in range(12, 16):
        for x in range(2, 7):
            d.set(x, 5, z, "smooth_quartz_slab[type=bottom,waterlogged=false]")
    posts(d, [(2, 15), (6, 15), (2, 12), (6, 12)], 2, 4, "light_gray_concrete")
    compost_bay(d, 3, 2, 13)
    d.set(3, 2, 14, "barrel[facing=up,open=false]")
    for x in range(1, 11):
        for z in range(17, 22):
            rim = x in (1, 10) or z in (17, 21)
            d.set(x, 2, z, "smooth_quartz_slab[type=bottom,waterlogged=false]" if rim else AIR)
            if not rim:
                if z == 19:
                    d.set(x, 1, z, "water")
                else:
                    d.set(x, 1, z, "farmland[moisture=7]")
                    d.set(x, 2, z, ("wheat[age=7]", "carrots[age=7]", "beetroots[age=3]")[x % 3])
    lamp_post(d, 1, 1, 3)
    lamp_post(d, 11, 1, 3)
    for x in range(1, 12):
        if x not in (5, 6, 7):
            d.set(x, 2, 0, "smooth_quartz_slab[type=bottom,waterlogged=false]")
    # ---- L2: tool garage ----
    if L >= 2:
        ga = bld(d, 12, 3, 18, 9, floors=1, roof="flat", doors=[(15, 9, "s")], win=9,
                 pal=dict(wall="light_gray_concrete", post="gray_concrete", band="lime_concrete", accent="lime_concrete",
                          deck="smooth_quartz"))
        for x in range(13, 18):
            for y in (2, 3):
                d.set(x, y, 3, AIR)
            d.set(x, 4, 3, "iron_bars")
        door_cells(d).update({(x, 2, 4) for x in range(13, 18)})
        counter(d, ga, "e", 2, 1, [P.b("grindstone[face=floor,facing={f}]")] + [P.rack()] * min(3, need_racks(d)) +
            [P.b("anvil[facing=north]")])
        counter(d, ga, "w", 2, 1, [P.b("barrel[facing=up,open=false]", "barrel[facing=up,open=false]"), P.b("chest[facing={f},type=single,waterlogged=false]")])
        cart(d, 15, 6, "z", "melon")
    # ---- L3: hydroponic greenhouse with the grain barrels ----
    if L >= 3:
        gh = bld(d, 12, 12, 24, 22, floors=1, fh=5, roof="flat", doors=[(18, 12, "n")], win=99,
                 wallfn=glasswall("Neoterra"), lamps=False)
        d.fill(13, 7, 13, 23, 7, 21, "light_blue_stained_glass")
        for z in (14, 16, 18, 20):
            for x in range(15, 23):
                d.set(x, 1, z, "farmland[moisture=7]")
                d.set(x, 2, z, ("carrots[age=7]", "beetroots[age=3]", "wheat[age=7]", "potatoes[age=7]")[z % 4])
                if x % 2:
                    d.set(x, 5, z, "end_rod[facing=down]")
        for z in range(14, 18):
            d.item(13, 2, z, "barrel")
        rack_bay(d, gh, "w", 2, 0)
        d.set(23, 2, 21, "water_cauldron[level=3]")
        d.set(23, 2, 13, "composter[level=6]")
    # ---- L4: vertical farm tower, solar canopy ----
    if L >= 4:
        vt = bld(d, 27, 3, 33, 9, floors=4, roof="flat", doors=[(30, 9, "s")], wallfn=glasswall("Neoterra"),
                 lamps=False)
        for k in range(4):
            y = 2 + 4 * k
            for z in (5, 7):
                for x in range(28, 33):
                    if (x, z) != (32, 7):
                        d.set(x, y, z, "moss_block")
                        d.set(x, y + 1, z, ("sweet_berry_bush[age=3]", "azalea", "fern", "flowering_azalea")[(x + k) % 4])
            d.set(29, y + 2, 6, "end_rod[facing=down]")
            d.set(31, y + 2, 6, "end_rod[facing=down]")
        for x in range(36, 43):
            for z in range(3, 10):
                d.set(x, 5, z, "daylight_detector[inverted=false,power=0]" if (x + z) % 2 else "smooth_quartz_slab[type=bottom,waterlogged=false]")
        posts(d, [(36, 3), (42, 3), (36, 9), (42, 9)], 2, 4, "light_gray_concrete")
        cart(d, 38, 6, "x", "melon")
        cart(d, 38, 8, "x", "pumpkin")
    # ---- L5: seed bank & packing hall, green roof, drone pad, trees ----
    if L >= 5:
        sb = bld(d, 27, 13, 41, 25, floors=2, roof="flat", doors=[(34, 13, "n")], ribbon=True,
                 pal=dict(wall="brown_terracotta", post="birch_planks", band="lime_concrete", accent="lime_concrete",
                          deck="moss_block"))
        counter(d, sb, "s", 2, 0, [P.b("barrel[facing=up,open=false]", "barrel[facing=up,open=false]")] * 6)
        counter(d, sb, "e", 2, 1, [P.books()] * 4)
        for x in range(30, 39, 3):
            d.set(x, 2, 18, "smooth_quartz_slab[type=top,waterlogged=false]")
            d.set(x + 1, 2, 18, "smooth_quartz_slab[type=top,waterlogged=false]")
            d.set(x, 3, 18, "melon")
            d.set(x + 1, 3, 18, "pumpkin")
        stairs_up(d, 28, 16, "south", 2, rail=False)
        counter(d, sb, "n", 6, 2, [P.b("smooth_quartz_slab[type=top,waterlogged=false]", "potted_bamboo"),
                            P.b("lectern[facing={f},has_book=true,powered=false]"), P.chair("birch"),
                            P.b("cartography_table")])
        floor_rug(d, sb, 6, ("lime_carpet", "white_carpet"), inset=3)
        for x in range(28, 41):
            for z in range(14, 25):
                if (x + z) % 5 == 0:
                    d.set(x, 11, z, "moss_carpet")
        for x, z in ((14, 26), (20, 26), (2, 26), (8, 26), (14, 33), (20, 33), (2, 33), (8, 33)):
            tree(d, x, z, 4, "azalea_leaves", "birch_log", 2)
        flowerbed(d, 26, 28, 42, 30)
        for x in (27, 33, 39):
            lamp_post(d, x, 32, 3)
            bench(d, x + 1, 33, "south", 2)
    return d


@design("farmer")
def farmer(pack, rel, L):
    d = globals()[f"farmer_{pack.lower()}"](rel, L)
    economize(d)
    return d
