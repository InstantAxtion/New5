"""
Trades group: builder, sawmill, lumberjack, fletcher, warehouse, deliveryman, composter.

Every type grows into a small complex: L1 is one modest, complete building; each level adds storeys, wings and
further buildings with furnished rooms that fit the trade (offices, stores, workshops, staff rooms, yards).
The per-type docstrings describe each pack's design.

The module-level toolkit below (build / Room / decor helpers) draws pack-styled buildings with storeys, stair
cores, windows, roofs and lights, and furnishes rooms along their walls while keeping a walking lane free.
"""
from hm import Design, design, AIR, D4, OPP, CW


# =============================================================================================== block helpers
def st(m, facing, half="bottom", shape="straight"):
    """Stairs state for material m ("spruce", "deepslate_tile", "smooth_quartz" ...)."""
    return f"{m}_stairs[facing={facing},half={half},shape={shape},waterlogged=false]"


def sl(m, t="bottom"):
    return f"{m}_slab[type={t},waterlogged=false]"


def tr(m, facing, half="top", open_=False):
    return f"{m}_trapdoor[facing={facing},half={half},open={'true' if open_ else 'false'},powered=false,waterlogged=false]"


def lg(m, axis="y"):
    return f"{m}[axis={axis}]"


def leaves(kind="oak"):
    return f"{kind}_leaves[distance=1,persistent=true,waterlogged=false]"


LANT = "lantern[hanging=true,waterlogged=false]"
LANT_S = "lantern[hanging=false,waterlogged=false]"
SLANT = "soul_lantern[hanging=true,waterlogged=false]"
CHAIN = "chain[axis=y,waterlogged=false]"
FLOWERS = ("poppy", "dandelion", "cornflower", "allium", "oxeye_daisy", "azure_bluet", "red_tulip", "lily_of_the_valley")
CHISEL = ("chiseled_bookshelf[facing={f},slot_0_occupied=true,slot_1_occupied=false,slot_2_occupied=true,"
          "slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")


def ring(x1, z1, x2, z2):
    out = []
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                out.append((x, z))
    return out


def rack_col(d, x, z, y, h=3, facing="north"):
    for k in range(h):
        d.rack(x, y + k, z, facing)
    return h


def rack_line(d, cells, y, need, h=3, facing="north"):
    """Rack columns on the given (x, z) cells until `need` racks are placed. Returns racks placed."""
    n = 0
    for x, z in cells:
        if n >= need:
            break
        n += rack_col(d, x, z, y, h, facing)
    return n


def aisles(d, x1, z1, x2, z2, y, need, h=3, along="z"):
    """Shelving: double rows of rack columns running `along`, 1-wide walkways between (walkway first).
    Fills row pair by row pair until `need` racks are placed; returns racks placed."""
    n = 0
    if along == "z":
        across, length = list(range(x1, x2 + 1)), range(z1, z2 + 1)
    else:
        across, length = list(range(z1, z2 + 1)), range(x1, x2 + 1)
    rows = [a for i, a in enumerate(across) if i % 3 != 0]
    for a in rows:
        if n >= need:
            break
        for b in length:
            x, z = (a, b) if along == "z" else (b, a)
            n += rack_col(d, x, z, y, h, "north" if along == "z" else "west")
    return n


def run_stairs(d, x, z, y, steps, direction, m, fill=None):
    """Straight flight: first stair at (x, y, z) rising one per cell toward `direction`; supports below, 3 cells
    cleared above every step. Returns the landing cell."""
    dx, dz = D4[direction]
    for i in range(steps):
        cx, cz = x + dx * i, z + dz * i
        yy = y + i
        d.set(cx, yy, cz, st(m, direction))
        if fill:
            for k in range(y, yy):
                d.set(cx, k, cz, fill)
        for k in range(1, 4):
            d.set(cx, yy + k, cz, AIR)
    return x + dx * steps, z + dz * steps


def log_pile(d, x1, z1, x2, z2, y, h, wood="spruce_log", axis="x"):
    """Stacked logs lying along `axis`, stepped (each row one narrower)."""
    for k in range(h):
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                inner = (axis == "x" and z1 + k <= z <= z2 - k) or (axis == "z" and x1 + k <= x <= x2 - k)
                if k == 0 or inner:
                    d.set(x, y + k, z, lg(wood, axis))


def sawhorse(d, x, z, y, m="oak", along="x"):
    dx, dz = (1, 0) if along == "x" else (0, 1)
    d.set(x, y, z, f"{m}_fence")
    d.set(x + 2 * dx, y, z + 2 * dz, f"{m}_fence")
    for k in range(3):
        d.set(x + k * dx, y + 1, z + k * dz, lg(f"stripped_{m}_log", along))


def chopping_block(d, x, z, y, log="oak_log"):
    d.set(x, y, z, lg(log, "y"))
    d.set(x, y + 1, z, "lever[face=floor,facing=north,powered=false]")


# =============================================================================================== exterior decor
def tree(d, x, z, y, kind="oak", h=4, r=2):
    """Small tree: trunk of h logs and a rounded crown."""
    for k in range(h):
        d.set(x, y + k, z, lg(f"{kind}_log", "y"))
    top = y + h
    for dy in (-2, -1, 0, 1):
        rr = r if dy < 0 else r - 1 if dy == 0 else 0
        for dx in range(-rr, rr + 1):
            for dz in range(-rr, rr + 1):
                if abs(dx) == rr and abs(dz) == rr and rr > 1:
                    continue
                cx, cy, cz = x + dx, top + dy, z + dz
                if d.bp.inside(cx, cy, cz) and d.air(cx, cy, cz):
                    d.set(cx, cy, cz, leaves(kind))
    if d.air(x, top, z):
        d.set(x, top, z, leaves(kind))


def bush(d, x, z, y, kind="oak"):
    d.set(x, y, z, leaves(kind))


def lamp_post(d, x, z, y, pack, h=3):
    if pack == "Neoterra":
        for k in range(h):
            d.set(x, y + k, z, "light_gray_concrete")
        d.set(x, y + h, z, "sea_lantern")
        d.set(x, y + h + 1, z, sl("smooth_quartz"))
    else:
        wood = "dark_oak" if pack == "Hearthwood" else "spruce"
        base = "stone_bricks" if pack == "Hearthwood" else "cobblestone"
        d.set(x, y, z, base)
        for k in range(1, h):
            d.set(x, y + k, z, f"{wood}_fence")
        d.set(x, y + h, z, LANT_S)


def bench(d, x, z, y, back, n=2, wood="oak", sit=True):
    """Outdoor bench of n seats along the side perpendicular to `back`, with trapdoor arms."""
    ax = (1, 0) if back in ("north", "south") else (0, 1)
    for i in range(n):
        d.chair(x + ax[0] * i, y, z + ax[1] * i, back, wood, sit)
    for side, k in ((-1, -1), (1, n)):
        cx, cz = x + ax[0] * k, z + ax[1] * k
        if d.air(cx, y, cz):
            f = ("west" if side < 0 else "east") if ax[0] else ("north" if side < 0 else "south")
            d.set(cx, y, cz, tr(wood, f, "bottom", True))


def flower_bed(d, x1, z1, x2, z2, y, edge=None, seed=0):
    """Bed of flowers on grass at y-1 (the ground), optional edging slab ring."""
    i = seed
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            d.set(x, y - 1, z, "grass_block[snowy=false]")
            if edge and (x in (x1, x2) or z in (z1, z2)):
                d.set(x, y, z, edge)
            else:
                d.set(x, y, z, FLOWERS[i % len(FLOWERS)] if (x + z + seed) % 3 else "short_grass")
            i += 1


def hedge(d, cells, y, kind="oak"):
    for x, z in cells:
        d.set(x, y, z, leaves(kind))


def path(d, x1, z1, x2, z2, block, border=None):
    """Paved path at ground level (gy), optional border on the long sides."""
    gy = d.gy
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for z in range(min(z1, z2), max(z1, z2) + 1):
            d.set(x, gy, z, block)
    if border:
        if x2 - x1 >= z2 - z1:
            for x in range(min(x1, x2), max(x1, x2) + 1):
                for z in (min(z1, z2) - 1, max(z1, z2) + 1):
                    if d.bp.inside(x, gy, z):
                        d.set(x, gy, z, border)
        else:
            for z in range(min(z1, z2), max(z1, z2) + 1):
                for x in (min(x1, x2) - 1, max(x1, x2) + 1):
                    if d.bp.inside(x, gy, z):
                        d.set(x, gy, z, border)


def wagon(d, x, z, y, wood="spruce", load="hay_block[axis=x]", along="x"):
    """Hand cart / wagon: plank bed on trapdoor 'wheels', a load on top, shafts in front."""
    dx, dz = (1, 0) if along == "x" else (0, 1)
    for k in range(3):
        cx, cz = x + dx * k, z + dz * k
        d.set(cx, y, cz, sl(wood, "top"))
        d.set(cx, y + 1, cz, load if k > 0 else f"{wood}_trapdoor[facing={'west' if along == 'x' else 'north'},half=bottom,open=true,powered=false,waterlogged=false]")
    d.set(x - dx, y, z - dz, f"{wood}_fence")


def crate_stack(d, x, z, y, n=2, top=None):
    for k in range(n):
        d.keg(x, y + k, z, "up" if k % 2 == 0 else "north")
    if top:
        d.set(x, y + n, z, top)


# =============================================================================================== buildings
STY = {
    "Neoterra": dict(wall="white_concrete", wall0="white_concrete", post="light_gray_concrete",
                     band="cyan_terracotta", floor="polished_diorite", ufloor="smooth_stone", plinth=None,
                     wood="birch", stair="smooth_quartz", glass="glass_pane", glass_up="glass_pane"),
    "Hearthwood": dict(wall="calcite", wall0="bricks", post="stripped_dark_oak_log[axis=y]", band="dark_oak_planks",
                       floor="oak_planks", ufloor="spruce_planks", plinth="stone_bricks", wood="dark_oak",
                       stair="dark_oak", glass="glass_pane", glass_up="glass_pane",
                       roof=("deepslate_tile_stairs", "deepslate_tile_slab"), end="calcite"),
    "Cascadia": dict(wall=None, wall0=None, post="spruce_log[axis=y]", band="stripped_spruce_wood[axis=y]",
                     floor="spruce_planks", ufloor="spruce_planks", plinth="cobblestone", wood="spruce",
                     stair="spruce", glass="glass_pane", glass_up="glass_pane",
                     roof=("dark_oak_stairs", "dark_oak_slab"), end="spruce_planks"),
}


class B:
    """A built building: geometry + helpers. fy[s] is the floor block of storey s, stand height fy[s]+1."""

    def __init__(self, d, x1, z1, x2, z2, storeys, H, y0, core, axis):
        self.d, self.x1, self.z1, self.x2, self.z2 = d, x1, z1, x2, z2
        self.storeys, self.H, self.y0, self.core, self.axis = storeys, H, y0, core, axis
        self.fy = [y0 - 1 + s * H for s in range(storeys + 1)]
        self.yr = self.fy[storeys]
        self.ridge = self.yr
        self.keep = set()
        if core:
            sx, sz = core
            for x in range(sx - 1, sx + 3):
                for z in range(sz - 2, sz + 6):
                    self.keep.add((x, z))

    def stand(self, s):
        return self.fy[s] + 1

    def room(self, s, x1=None, z1=None, x2=None, z2=None):
        return Room(self.d, self.x1 + 1 if x1 is None else x1, self.z1 + 1 if z1 is None else z1,
                    self.x2 - 1 if x2 is None else x2, self.z2 - 1 if z2 is None else z2, self.stand(s),
                    self.H - 1, keep=self.keep)

    def door(self, x, z, facing, double=False, hood=True, lamps=True):
        """Door in the ground storey wall at (x, z) opening outward to `facing`; a hood and two lanterns."""
        d, P = self.d, STY[self.d.pack]
        y = self.stand(0)
        if double:
            along = "x" if facing in ("north", "south") else "z"
            d.double_door(x, y, z, along, OPP[facing], P["wood"])
            xs = [(x, z), (x + (1 if along == "x" else 0), z + (1 if along == "z" else 0))]
        else:
            d.door(x, y, z, OPP[facing], P["wood"])
            xs = [(x, z)]
        ox, oz = D4[facing]
        for cx, cz in xs:                                   # keep the step in front of the door clear
            for k in range(3):
                if d.bp.inside(cx + ox, y + k, cz + oz):
                    d.set(cx + ox, y + k, cz + oz, AIR)
        side = CW[facing]
        sx, sz = D4[side]
        cells = [(xs[0][0] - sx, xs[0][1] - sz)] + xs + [(xs[-1][0] + sx, xs[-1][1] + sz)]
        if hood and self.H >= 4:
            for cx, cz in cells:
                hx, hz = cx + ox, cz + oz
                if d.bp.inside(hx, y + 2, hz) and d.air(hx, y + 2, hz):
                    if d.pack == "Neoterra":
                        d.set(hx, y + 2, hz, sl("smooth_quartz", "top"))
                    else:
                        d.set(hx, y + 2, hz, st(P["wood"], OPP[facing], "top"))
            if lamps:
                for cx, cz in (cells[0], cells[-1]):
                    hx, hz = cx + ox, cz + oz
                    if d.bp.inside(hx, y + 1, hz) and d.air(hx, y + 1, hz):
                        d.set(hx, y + 1, hz, LANT if d.pack != "Neoterra" else SLANT)
        return xs

    def opening(self, x1, z1, x2, z2, h=3, frame=None):
        """Large open doorway / cart door in the ground storey wall (air), with a lintel beam above."""
        d = self.d
        y = self.stand(0)
        out = (0, -1) if z1 == self.z1 else (0, 1) if z1 == self.z2 else (-1, 0) if x1 == self.x1 else (1, 0)
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for z in range(min(z1, z2), max(z1, z2) + 1):
                for k in range(h):
                    d.set(x, y + k, z, AIR)
                    if d.bp.inside(x + out[0], y + k, z + out[1]):
                        d.set(x + out[0], y + k, z + out[1], AIR)
                if frame:
                    d.set(x, y + h, z, frame)

    def partition(self, s, x1, z1, x2, z2, doors=(), block=None, glass=False):
        """Interior wall on storey s along a line (x1==x2 or z1==z2) with door cells."""
        d, P = self.d, STY[self.d.pack]
        y = self.stand(s)
        block = block or (P["wall"] or "spruce_planks")
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for z in range(min(z1, z2), max(z1, z2) + 1):
                for k in range(self.H - 1):
                    d.set(x, y + k, z, ("glass_pane" if glass and k > 0 else block))
        for x, z in doors:
            facing = "south" if z1 == z2 else "east"
            d.door(x, y, z, facing, P["wood"])
            for k in range(2, self.H - 1):
                d.set(x, y + k, z, block)


def build(d, x1, z1, x2, z2, storeys=1, H=4, axis="x", roof="gable", core=None, y0=2, windows=True,
          ends=True, chimney=None, wall=None, wall0=None, overhang=1, skip_windows=(), street_glass=False):
    """Pack-styled building. roof: 'gable' (ridge along `axis`), 'flat', 'none'. core: (sx, sz) of a 2-wide
    switchback stair core occupying x sx..sx+1, z sz-1..sz+4. chimney: (x, z, inward) hearth against a wall."""
    P = STY[d.pack]
    b = B(d, x1, z1, x2, z2, storeys, H, y0, core, axis)
    pk = d.pack
    rg = ring(x1, z1, x2, z2)
    corners = {(x1, z1), (x2, z1), (x1, z2), (x2, z2)}
    yr = b.yr
    # floor slab on the ground
    d.fill(x1, y0 - 1, z1, x2, y0 - 1, z2, P["floor"])
    for s in range(storeys):
        fy = b.fy[s]
        top = fy + H - 1
        for x, z in rg:
            ax = "x" if z in (z1, z2) else "z"
            for y in range(fy + 1, top + 1):
                if pk == "Cascadia":
                    blk = lg("stripped_spruce_log", ax)
                elif pk == "Hearthwood":
                    blk = (wall0 or P["wall0"]) if (s == 0 and storeys > 1) else (wall or P["wall"])
                else:
                    blk = wall or P["wall"]
                d.set(x, y, z, blk)
            # posts / pilasters
            i = (x - x1) if z in (z1, z2) else (z - z1)
            step = {"Neoterra": 4, "Hearthwood": 3 if (s > 0 or storeys == 1) else 99, "Cascadia": 4}[pk]
            if (x, z) in corners or i % step == 0:
                for y in range(fy + 1, top + 1):
                    d.set(x, y, z, P["post"] if not (pk == "Hearthwood" and s == 0 and storeys > 1) else "stone_bricks")
        if s == 0 and P["plinth"]:
            for x, z in rg:
                d.set(x, y0, z, P["plinth"] if (x * 7 + z * 3) % 5 else ("mossy_cobblestone" if pk == "Cascadia" else "andesite"))
        if s > 0:
            d.fill(x1 + 1, fy, z1 + 1, x2 - 1, fy, z2 - 1, P["ufloor"])
            for x, z in rg:
                if pk == "Hearthwood":
                    d.set(x, fy, z, lg("stripped_dark_oak_log", "x" if z in (z1, z2) else "z"))
                elif pk == "Cascadia":
                    d.set(x, fy, z, lg("spruce_log", "x" if z in (z1, z2) else "z"))
                else:
                    d.set(x, fy, z, P["band"])
        # windows
        if windows:
            for side in ("north", "south", "west", "east"):
                if side in skip_windows and s == 0:
                    continue
                if side in ("north", "south"):
                    zz = z1 if side == "north" else z2
                    cells = [(x, zz) for x in range(x1 + 1, x2)]
                else:
                    xx = x1 if side == "west" else x2
                    cells = [(xx, z) for z in range(z1 + 1, z2)]
                for i, (x, z) in enumerate(cells):
                    if pk == "Neoterra":
                        if (i + 1) % 4 == 0 or i in (0, len(cells) - 1):
                            continue
                        lo = fy + 1 if (street_glass and s == 0 and side == "north") else fy + 2
                        d.window(x, lo, z, x, top, z, P["glass"] if s == 0 else P["glass_up"])
                        ox, oz = D4[side]
                        if s > 0 and d.bp.inside(x + ox, fy + 1, z + oz):
                            d.set(x + ox, fy + 1, z + oz, sl("smooth_quartz", "top"))
                    else:
                        if i % 3 != 1 or i >= len(cells) - 1:
                            continue
                        d.window(x, fy + 2, z, x, fy + 3 if H >= 4 else fy + 2, z, P["glass"])
                        ox, oz = D4[side]
                        out = (x + ox, z + oz)
                        if not d.bp.inside(out[0], fy + 1, out[1]):
                            continue
                        if pk == "Cascadia":
                            for sd in (CW[side], OPP[CW[side]]):
                                sx_, sz_ = D4[sd]
                                for k in (2, 3):
                                    c = (x + ox + sx_, fy + k, z + oz + sz_)
                                    if H >= 4 and d.bp.inside(*c) and d.air(*c):
                                        d.set(*c, tr("spruce", sd, "bottom", True))
                        if s > 0 or side == "north":
                            if d.air(out[0], fy + 1, out[1]) and d.air(out[0], fy + 2, out[1]):
                                d.set(out[0], fy + 1, out[1], tr(P["wood"], side, "top"))
                                d.set(out[0], fy + 2, out[1], "potted_" + FLOWERS[(x + z) % 6])
    # roof
    if roof == "flat":
        d.fill(x1, yr, z1, x2, yr, z2, "smooth_quartz" if pk == "Neoterra" else P["ufloor"])
        for x, z in rg:
            d.set(x, yr + 1, z, P["wall"] or "spruce_planks")
            d.set(x, yr + 2, z, sl("smooth_quartz" if pk == "Neoterra" else "spruce"))
        b.ridge = yr + 2
    elif roof == "gable":
        for x, z in rg:
            d.set(x, yr, z, lg("stripped_dark_oak_log" if pk == "Hearthwood" else "spruce_log",
                               "x" if z in (z1, z2) else "z") if pk != "Neoterra" else P["post"])
        rs, rsl = P.get("roof", ("smooth_quartz_stairs", "smooth_quartz_slab"))
        b.ridge = d.gable(x1, z1, x2, z2, yr + 1, axis, rs, rsl, P.get("end", "white_concrete"), overhang=overhang)
        # gable end detailing
        if ends:
            if axis == "x":
                ends_cells = [(x, z) for x in (x1, x2) for z in range(z1, z2 + 1)]
                mid = (z1 + z2) // 2
            else:
                ends_cells = [(x, z) for z in (z1, z2) for x in range(x1, x2 + 1)]
                mid = (x1 + x2) // 2
            for x, z in ends_cells:
                for y in range(yr + 1, b.ridge + 1):
                    if d.get(x, y, z) != "minecraft:" + P["end"]:
                        continue
                    c = z if axis == "x" else x
                    if pk == "Hearthwood" and (c - mid) % 2 == 0:
                        d.set(x, y, z, lg("stripped_dark_oak_log", "y"))
                    elif pk == "Cascadia" and c % 2 == 0:
                        d.set(x, y, z, lg("stripped_spruce_log", "y"))
            # attic vent window
            for e in ((x1, mid) if axis == "x" else (mid, z1), (x2, mid) if axis == "x" else (mid, z2)):
                yv = b.ridge - 2
                if yv > yr + 1 and not d.air(e[0], yv, e[1]):
                    d.set(e[0], yv, e[1], "glass_pane")
        # tie beams across the top storey for lamps
        if axis == "x":
            for x in range(x1 + 2, x2 - 1, 4):
                for z in range(z1 + 1, z2):
                    d.set(x, yr, z, lg("stripped_dark_oak_log" if pk == "Hearthwood" else "stripped_spruce_log", "z"))
        else:
            for z in range(z1 + 2, z2 - 1, 4):
                for x in range(x1 + 1, x2):
                    d.set(x, yr, z, lg("stripped_dark_oak_log" if pk == "Hearthwood" else "stripped_spruce_log", "x"))
    # Neoterra ceiling lights (froglights are walkable on the floor above)
    if pk == "Neoterra":
        for s in range(1, storeys + 1):
            yy = b.fy[s]
            for x in range(x1 + 2, x2 - 1, 4):
                for z in range(z1 + 2, z2 - 1, 4):
                    if b.core and (x, z) in b.keep:
                        continue
                    d.set(x, yy, z, "pearlescent_froglight[axis=y]" if (s < storeys or roof != "flat") else "sea_lantern")
    # stair core
    if core:
        sx, sz = core
        for s in range(storeys - 1):
            fy = b.fy[s]
            if s % 2 == 0:
                run_stairs(d, sx, sz, fy, 4, "south", P["stair"], fill=(P["ufloor"] if s == 0 else None))
            else:
                run_stairs(d, sx + 1, sz + 3, fy, 4, "north", P["stair"])
        if storeys > 1:
            # railing on the far side of each stair hole (away from the landings)
            pass
    # chimney / fireplace
    if chimney:
        cx, cz, inward = chimney
        frame = {"Neoterra": "polished_blackstone_bricks", "Hearthwood": "bricks", "Cascadia": "cobblestone"}[pk]
        fire = "soul_campfire" if pk == "Neoterra" else "campfire"
        d.hearth(cx, y0, cz, inward, y0 + 2, frame, fire)
        wx, wz = cx - D4[inward][0], cz - D4[inward][1]          # wall cell behind the fire
        top = b.ridge + 2
        for y in range(y0 + 2, top + 1):
            d.set(cx, y, cz, frame) if y < yr else None
            d.set(wx, y, wz, frame)
        d.set(wx, top + 1, wz, {"Neoterra": "polished_blackstone_brick_wall", "Hearthwood": "brick_wall",
                               "Cascadia": "cobblestone_wall"}[pk])
        for s in range(1, storeys):
            d.set(cx, b.fy[s], cz, frame)
        for k in (-1, 1):
            sx_, sz_ = D4[CW[inward]]
            b.keep.add((cx + sx_ * k + D4[inward][0], cz + sz_ * k + D4[inward][1]))
        b.keep.add((cx + D4[inward][0], cz + D4[inward][1]))
        b.keep.update({(cx, cz), (cx + D4[CW[inward]][0], cz + D4[CW[inward]][1]),
                       (cx - D4[CW[inward]][0], cz - D4[CW[inward]][1])})
    return b


def neo_roof(d, b, kind="solar"):
    """Roof-top features on a flat Neoterra roof: solar arrays, roof garden or plant (HVAC) units."""
    y = b.yr + 1
    x1, z1, x2, z2 = b.x1 + 2, b.z1 + 2, b.x2 - 2, b.z2 - 2
    if kind == "solar":
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1, 3):
                d.set(x, y, z, "daylight_detector[inverted=false,power=0]")
    elif kind == "garden":
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                d.set(x, y, z, "moss_carpet" if (x * 3 + z) % 5 else ("azalea" if (x + z) % 2 else "flowering_azalea"))
    elif kind == "hvac":
        for x in range(x1, min(x1 + 3, x2) + 1):
            for z in range(z1, min(z1 + 1, z2) + 1):
                d.set(x, y, z, "iron_block")
                d.set(x, y + 1, z, tr("iron", "north", "bottom"))
        for x in range(x1, x2 + 1, 3):
            for z in range(z1 + 3, z2 + 1, 3):
                d.set(x, y, z, "daylight_detector[inverted=false,power=0]")


# =============================================================================================== rooms
NOT_FLOOR = ("air", "stairs", "ladder", "trapdoor")


class Room:
    """Interior rectangle (inclusive) at standing height y. Furnishes along the walls (ring) while the second
    ring (lane) stays free; centre pieces go further in. Cells next to doors, stairs, holes and the building's
    keep zones are never used."""

    def __init__(self, d, x1, z1, x2, z2, y, h=3, keep=()):
        self.d, self.x1, self.z1, self.x2, self.z2, self.y, self.h = d, x1, z1, x2, z2, y, h
        self.used = set()
        self.keep = set(k for k in keep if x1 <= k[0] <= x2 and z1 <= k[1] <= z2)
        for x in range(x1 - 1, x2 + 2):
            for z in range(z1 - 1, z2 + 2):
                if not d.bp.inside(x, y, z):
                    continue
                n = d.get(x, y, z)
                below = d.get(x, y - 1, z)
                inside = x1 <= x <= x2 and z1 <= z <= z2
                opening = (not inside) and n == AIR and d.air(x, y + 1, z) and below != AIR
                if any(k in n for k in ("door", "stairs", "ladder", "blockhut")) or "stairs" in below \
                        or opening or (inside and (below == AIR or "stairs" in below)):
                    for dx in (-1, 0, 1):
                        for dz in (-1, 0, 1):
                            self.keep.add((x + dx, z + dz))

    # -------------------------------------------------------------- slots
    def free(self, x, z, h=2):
        d = self.d
        if (x, z) in self.keep or (x, z) in self.used:
            return False
        if not (self.x1 <= x <= self.x2 and self.z1 <= z <= self.z2):
            return False
        return all(d.air(x, self.y + k, z) for k in range(h)) and d.get(x, self.y - 1, z) != AIR

    def is_corner(self, x, z):
        return x in (self.x1, self.x2) and z in (self.z1, self.z2)

    def ring(self, sides=("north", "east", "south", "west")):
        x1, z1, x2, z2 = self.x1, self.z1, self.x2, self.z2
        seq = []
        for s in sides:
            if s == "north":
                seq += [((x, z1), "south") for x in range(x1 + 1, x2)]
            elif s == "east":
                seq += [((x2, z), "west") for z in range(z1 + 1, z2)]
            elif s == "south":
                seq += [((x, z2), "north") for x in range(x2 - 1, x1, -1)]
            else:
                seq += [((x1, z), "east") for z in range(z2 - 1, z1, -1)]
        return seq

    def slots(self, sides=("north", "east", "south", "west"), h=2):
        return [(c, f) for c, f in self.ring(sides) if self.free(*c, h=h)]

    def take(self, sides=("north", "east", "south", "west"), h=2):
        s = self.slots(sides, h)
        if not s:
            return None
        c, f = s[0]
        self.used.add(c)
        return c, f

    # -------------------------------------------------------------- placing
    def item(self, name, n=1, sides=("north", "east", "south", "west")):
        """Required work blocks along the walls. Returns how many were placed."""
        k = 0
        for _ in range(n):
            t = self.take(sides)
            if not t:
                break
            (x, z), f = t
            self.d.item(x, self.y, z, name, f if name != "barrel" else f)
            k += 1
        return k

    def racks(self, need, h=3, sides=("north", "east", "south", "west")):
        n = 0
        while n < need:
            t = self.take(sides, h=h)
            if not t:
                break
            (x, z), f = t
            n += rack_col(self.d, x, z, self.y, h, f)
        return n

    def barrels(self, need, h=3, sides=("north", "east", "south", "west")):
        n = 0
        while n < need:
            t = self.take(sides, h=h)
            if not t:
                break
            (x, z), f = t
            for k in range(h):
                if n < need:
                    self.d.item(x, self.y + k, z, "barrel", f)
                    n += 1
        return n

    def books(self, need, h=2, sides=("north", "east", "south", "west")):
        n = 0
        while n < need:
            t = self.take(sides, h=h)
            if not t:
                break
            (x, z), f = t
            k = min(h, need - n)
            self.d.bookshelf(x, self.y, z, k)
            if k < h:
                self.d.set(x, self.y + k, z, "potted_fern")
            n += k
        return n

    def bed(self, wood, sides=("north", "east", "south", "west")):
        """Bed with its head against the wall, nightstand with a candle beside it."""
        d = self.d
        for (x, z), f in self.ring(sides):
            fx, fz = D4[f]
            if self.free(x, z) and self.free(x + fx, z + fz) and not self.is_corner(x, z):
                d.bed(x, self.y, z, OPP[f])
                self.used.update({(x, z), (x + fx, z + fz)})
                for sx, sz in (D4[CW[f]], D4[OPP[CW[f]]]):
                    if self.free(x + sx, z + sz):
                        d.set(x + sx, self.y, z + sz, sl(wood, "top"))
                        d.candle(x + sx, self.y + 1, z + sz, 1)
                        self.used.add((x + sx, z + sz))
                        break
                return True
        return False

    def chairs_desk(self, n, wood, top=None, sit=True):
        """A desk (top slabs) against the wall with n chairs in front of it, facing the wall."""
        d = self.d
        placed = 0
        for (x, z), f in self.ring():
            if placed >= n:
                break
            fx, fz = D4[f]
            if self.free(x, z) and self.free(x + fx, z + fz) and not self.is_corner(x, z) \
                    and (x + fx, z + fz) not in self.keep:
                d.set(x, self.y, z, top or sl(wood, "top"))
                d.chair(x + fx, self.y, z + fz, OPP[f], wood, sit)
                self.used.update({(x, z), (x + fx, z + fz)})
                if placed % 2 == 0:
                    d.set(x, self.y + 1, z, "potted_cactus" if wood == "birch" else "candle[candles=2,lit=false,waterlogged=false]")
                placed += 1
        return placed

    def table_group(self, wood, seats=4, kind="post", rug=None, sit=True):
        """4-chair table somewhere in the centre region. Returns seats placed."""
        d = self.d
        for cz in range(self.z1 + 3, self.z2 - 2):
            for cx in range(self.x1 + 3, self.x2 - 2):
                cells = [(cx + a, cz + b) for a in (-1, 0, 1) for b in (-1, 0, 1)]
                if all(self.free(*c, h=2) for c in cells) and all(
                        self.free(cx + a, cz + b, 1) or (cx + a, cz + b) in self.used
                        for a in (-2, 2) for b in (0,)):
                    if rug:
                        d.rug(cx - 1, cz - 1, cx + 1, cz + 1, self.y, (rug,), "plain")
                    for c in cells:
                        if c != (cx, cz):
                            d.set(c[0], self.y, c[1], AIR) if "carpet" not in d.get(c[0], self.y, c[1]) else None
                    d.table(cx, self.y, cz, wood, kind)
                    k = 0
                    for side, (dx, dz) in D4.items():
                        if k >= seats:
                            break
                        d.chair(cx + dx, self.y, cz + dz, side, wood, sit)
                        k += 1
                    for a in range(-2, 3):
                        for b in range(-2, 3):
                            self.used.add((cx + a, cz + b))
                    return k
        return 0

    def center_line(self, blocks, along="x", y_off=0):
        """A run of blocks (workbench line) through the middle of the room, lanes kept on both sides."""
        d = self.d
        if along == "x":
            z = (self.z1 + self.z2) // 2
            xs = list(range(self.x1 + 2, self.x2 - 1))
            cells = [(x, z) for x in xs]
        else:
            x = (self.x1 + self.x2) // 2
            cells = [(x, z) for z in range(self.z1 + 2, self.z2 - 1)]
        k = 0
        for c in cells:
            if k >= len(blocks):
                break
            if self.free(*c):
                b = blocks[k]
                if callable(b):
                    b(c[0], self.y + y_off, c[1])
                else:
                    d.set(c[0], self.y + y_off, c[1], b)
                self.used.add(c)
                k += 1
        return k

    def corners(self, block):
        for x in (self.x1, self.x2):
            for z in (self.z1, self.z2):
                if self.free(x, z):
                    self.d.set(x, self.y, z, block)
                    self.used.add((x, z))

    def fill(self, kinds, sides=("north", "east", "south", "west"), every=1):
        """Decorate the remaining wall slots with a cycle of decor kinds (see DECOR)."""
        i = 0
        for (x, z), f in self.ring(sides):
            if not self.free(x, z):
                continue
            if i % every == 0:
                DECOR[kinds[(i // every) % len(kinds)]](self.d, x, self.y, z, f)
                self.used.add((x, z))
            i += 1

    def rug(self, colors, pattern="border"):
        x1, z1, x2, z2 = self.x1 + 2, self.z1 + 2, self.x2 - 2, self.z2 - 2
        if x2 - x1 < 1 or z2 - z1 < 1:
            return
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if (x, z) in self.keep or (x, z) in self.used or not self.d.air(x, self.y, z) \
                        or self.d.get(x, self.y - 1, z) == AIR:
                    continue
                k = 0 if pattern == "plain" else (0 if x in (x1, x2) or z in (z1, z2) else 1)
                self.d.set(x, self.y, z, colors[k % len(colors)])

    def lights(self, step=4, soul=False):
        """Hanging lanterns (on chains where the ceiling is high) on a grid where the ceiling allows."""
        d = self.d
        lamp = SLANT if soul else LANT
        y = self.y + 2
        for x in range(self.x1 + 1, self.x2, step):
            for z in range(self.z1 + 1, self.z2, step):
                if not d.air(x, y, z):
                    continue
                for top in range(y + 1, y + 6):
                    if not d.bp.inside(x, top, z):
                        break
                    n = d.get(x, top, z)
                    if n != AIR:
                        if "glass" in n or "lantern" in n or "chain" in n:
                            break
                        for k in range(y + 1, top):
                            d.set(x, k, z, CHAIN)
                        d.set(x, y, z, lamp)
                        break


def _shelf(d, x, y, z, f, wood="oak"):
    d.set(x, y, z, sl(wood, "top"))
    d.set(x, y + 1, z, ("decorated_pot[cracked=false,facing=%s,waterlogged=false]" % f) if (x + z) % 2
          else "potted_" + FLOWERS[(x * 3 + z) % 8])


DECOR = {
    "shelf_oak": lambda d, x, y, z, f: _shelf(d, x, y, z, f, "oak"),
    "shelf_dark": lambda d, x, y, z, f: _shelf(d, x, y, z, f, "dark_oak"),
    "shelf_spruce": lambda d, x, y, z, f: _shelf(d, x, y, z, f, "spruce"),
    "shelf_birch": lambda d, x, y, z, f: _shelf(d, x, y, z, f, "birch"),
    "shelf_quartz": lambda d, x, y, z, f: (d.set(x, y, z, sl("smooth_quartz", "top")),
                                           d.set(x, y + 1, z, "potted_bamboo" if (x + z) % 2 else "white_candle[candles=3,lit=false,waterlogged=false]")),
    "keg": lambda d, x, y, z, f: (d.keg(x, y, z, f), d.keg(x, y + 1, z, "up") if (x + z) % 2 else None),
    "crate": lambda d, x, y, z, f: (d.keg(x, y, z, "up"), d.set(x, y + 1, z, "white_wool" if (x + z) % 2 else "brown_wool")),
    "sack": lambda d, x, y, z, f: (d.set(x, y, z, "brown_wool" if (x + z) % 2 else "white_wool"),
                                   d.set(x, y + 1, z, "brown_carpet") if (x + z) % 3 == 0 else None),
    "plant": lambda d, x, y, z, f: d.set(x, y, z, "potted_fern" if (x + z) % 2 else "potted_azalea_bush"),
    "bamboo": lambda d, x, y, z, f: d.set(x, y, z, "potted_bamboo"),
    "chisel": lambda d, x, y, z, f: (d.set(x, y, z, CHISEL.format(f=f)), d.candle(x, y + 1, z, 2)),
    "cauldron": lambda d, x, y, z, f: d.set(x, y, z, "water_cauldron[level=2]"),
    "logs": lambda d, x, y, z, f: (d.set(x, y, z, lg("oak_log", "x" if f in ("north", "south") else "z")),
                                   d.set(x, y + 1, z, lg("stripped_oak_log", "x" if f in ("north", "south") else "z"))),
    "planks": lambda d, x, y, z, f: (d.set(x, y, z, "spruce_planks"), d.set(x, y + 1, z, sl("spruce"))),
    "stone": lambda d, x, y, z, f: (d.set(x, y, z, "stone_bricks"), d.set(x, y + 1, z, sl("stone_brick"))),
    "lamp": lambda d, x, y, z, f: (d.set(x, y, z, sl("spruce", "top")), d.set(x, y + 1, z, LANT_S)),
    "hay": lambda d, x, y, z, f: d.set(x, y, z, "hay_block[axis=y]"),
    "wardrobe": lambda d, x, y, z, f: (d.set(x, y, z, "barrel[facing=%s,open=false]" % f),
                                       d.set(x, y + 1, z, tr("spruce", f, "bottom", True)) if False else
                                       d.set(x, y + 1, z, "barrel[facing=%s,open=false]" % f)),
    "banner_red": lambda d, x, y, z, f: (d.set(x, y, z, "potted_red_tulip"), d.banner(x, y + 2, z, f, "red")
                                         if d.air(x, y + 2, z) else None),
    "banner_cyan": lambda d, x, y, z, f: (d.set(x, y, z, "potted_bamboo"), d.banner(x, y + 2, z, f, "cyan")
                                          if d.air(x, y + 2, z) else None),
    "banner_green": lambda d, x, y, z, f: (d.set(x, y, z, "potted_fern"), d.banner(x, y + 2, z, f, "green")
                                           if d.air(x, y + 2, z) else None),
}

PACK_DECOR = {
    "Neoterra": ["shelf_quartz", "bamboo", "banner_cyan", "crate"],
    "Hearthwood": ["shelf_dark", "keg", "banner_red", "plant"],
    "Cascadia": ["shelf_spruce", "keg", "banner_green", "plant"],
}
WOOD = {"Neoterra": "birch", "Hearthwood": "dark_oak", "Cascadia": "spruce"}
RUG = {"Neoterra": ("light_gray_carpet", "cyan_carpet"), "Hearthwood": ("red_carpet", "orange_carpet"),
       "Cascadia": ("brown_carpet", "green_carpet")}


# =============================================================================================== BUILDER
"""
Builder
  Neoterra   "Construction office & yard": glass-fronted office tower (1 storey at L1 -> 3 storeys at L4) with the
             workshop and plan room downstairs, drafting library above, staff floor on top; materials hall with
             rack aisles (L3), prefab workshop (L4, upper canteen at L5), walled yard with stacks and a tower crane.
  Hearthwood "Master builder's yard": timber-framed workshop house (upper drafting floor from L2) with a brick
             chimney, a long tiled store barn with rack bays (L3, loft at L5), a stone mason's lodge (L4, upper
             floor at L5) around a gravel yard with timber and stone stacks, a saw horse and a hoist.
  Cascadia   "Timber framers' barn": tall gable-to-street barn with hay-hoist beam and loft (L2), a pole lumber
             shed (L3), a two-storey bunk & plan cabin with porch (L4), a smithy lean-to and log yard (L5).
"""
BRACKS = {1: 9, 2: 12, 3: 22, 4: 33, 5: 44}
BSEATS = {1: 2, 2: 4, 3: 4, 4: 8, 5: 8}


def builder_neo(rel, L):
    d = Design("Neoterra", rel, (36, 22, 30), paving="smooth_stone")
    P, y0 = "Neoterra", 2
    sto = {1: 1, 2: 2, 3: 2, 4: 3, 5: 4}[L]
    a = build(d, 3, 3, 17, 12, sto, roof="flat", core=(15, 5) if sto > 1 else None, street_glass=True)
    a.door(8, 3, "north", double=True)
    d.hut(4, y0, 4)
    d.sign(11, 6, 2, "north", ["BUILD", "& DESIGN"], "birch", glow=True, color="cyan")
    r0 = a.room(0)
    r0.item("crafting_table", sides=("west",))
    r0.item("cartography_table", sides=("west",))
    racks = r0.racks(BRACKS[L] if L <= 2 else 12, sides=("south",))
    r0.item("barrel", 2, sides=("south", "east"))
    if L >= 2:
        for it in ("smithing_table", "anvil", "grindstone", "stonecutter"):
            r0.item(it, sides=("south", "east", "north"))
        if L <= 3:
            r0.item("hopper", sides=("east", "north"))
    if L >= 5:
        r0.item("ender_chest", sides=("east", "north", "south"))
    r0.chairs_desk(2, "birch", top=sl("smooth_quartz", "top"))
    r0.table_group("birch", 4, "slab", rug="gray_carpet", sit=False)
    r0.fill(PACK_DECOR[P])
    if sto >= 2:
        r1 = a.room(1)
        r1.books(12, sides=("west", "south"))
        r1.item("lectern", sides=("north", "south", "east"))
        r1.item("cartography_table", sides=("north", "south", "east"))
        r1.item("crafting_table", sides=("north", "south", "east"))
        r1.chairs_desk(2, "birch", top=sl("smooth_quartz", "top"))
        r1.table_group("birch", 4, "slab", rug="cyan_carpet", sit=False)
        r1.fill(PACK_DECOR[P])
    if sto >= 3:
        r2 = a.room(2)
        r2.bed("birch", sides=("south",))
        r2.item("jukebox", sides=("south", "west"))
        r2.table_group("birch", 4, "slab", rug="light_gray_carpet")
        r2.chairs_desk(0, "birch")
        r2.fill(["shelf_quartz", "bamboo", "crate", "shelf_quartz", "banner_cyan"])
        if sto >= 4:                                                 # top: meeting room with a long table
            r3 = a.room(3)
            for x in range(7, 12):
                d.set(x, r3.y, 8, sl("smooth_quartz", "top"))
                d.chair(x, r3.y, 7, "north", "birch", sit=False)
                d.chair(x, r3.y, 9, "south", "birch", sit=False)
                r3.used.update({(x, 7), (x, 8), (x, 9)})
            r3.fill(["shelf_quartz", "bamboo", "banner_cyan"])
        neo_roof(d, a, "garden")
    else:
        neo_roof(d, a, "solar")
    # street front: planters with trees, benches, lamp posts
    for x in (1, 19):
        d.set(x, y0, 2, "moss_block")
        tree(d, x, 2, y0 + 1, "birch", 3, 1)
    bench(d, 4, 1, y0, "north", 2, "birch", sit=True)
    lamp_post(d, 2, 1, y0, P)
    path(d, 8, 0, 9, 2, "polished_andesite", border="cyan_terracotta")
    seats = 2 + (2 if sto >= 2 else 0) + (4 if sto >= 3 else 0)
    # ---- materials hall (L3+)
    if L >= 3:
        hb = build(d, 20, 3, 33, 15, 2 if L >= 5 else 1, H=5 if L < 5 else 4, roof="flat",
                   core=(31, 6) if L >= 5 else None)
        hb.opening(24, 3, 26, 3, 4, "yellow_concrete") if L < 5 else hb.opening(24, 3, 26, 3, 3, "yellow_concrete")
        for x in (23, 27):
            d.set(x, y0, 2, "yellow_concrete")
            d.set(x, y0 + 1, 2, "black_concrete")
        d.sign(25, hb.stand(0) + 3 if L < 5 else 6, 2, "north", ["MATERIALS", "STORE"], "birch", glow=True, color="yellow")
        need = BRACKS[L] - racks
        rh = hb.room(0)
        y1 = hb.stand(0)
        n = aisles(d, 21, 6, 29, 13, y1, min(need, 48 if L < 5 else 27))
        racks += n
        rh.keep |= {(x, z) for x in range(21, 30) for z in range(5, 15)}
        rh.fill(["stone", "planks", "crate", "logs"], sides=("north", "east"))
        if L >= 5:
            r5 = hb.room(1)
            racks += r5.racks(BRACKS[L] - racks, sides=("south", "west"))
            r5.table_group("birch", 4, "slab", rug="gray_carpet", sit=False)
            r5.fill(["crate", "shelf_quartz", "bamboo"])
            neo_roof(d, hb, "solar")
        else:
            neo_roof(d, hb, "hvac")
    # ---- prefab workshop (L4+), canteen above at L5
    if L >= 4:
        cs = 2 if L >= 5 else 1
        c = build(d, 3, 16, 17, 25, cs, roof="flat", core=(4, 18) if cs > 1 else None)
        c.door(10, 16, "north", double=True)
        rc = c.room(0)
        rc.item("domum_ornamentum:architectscutter", sides=("east", "south"))
        if racks < BRACKS[L]:
            racks += rc.racks(BRACKS[L] - racks, sides=("south",))
        rc.center_line([lg("stripped_birch_log", "x"), "crafting_table", sl("smooth_quartz", "top"),
                        "stonecutter[facing=north]", sl("smooth_quartz", "top"), lg("stripped_birch_log", "x")])
        rc.fill(["planks", "stone", "crate", "logs", "shelf_quartz"])
        if cs > 1:
            rcc = c.room(1)
            rcc.table_group("birch", 4, "slab", rug="cyan_carpet", sit=False)
            rcc.item("smoker", 1, sides=("south",)) if False else None
            for blk in ("smoker[facing=north,lit=false]", "water_cauldron[level=3]", sl("smooth_quartz", "top"),
                        "furnace[facing=north,lit=false]"):
                t = rcc.take(("south",))
                if t:
                    d.set(t[0][0], rcc.y, t[0][1], blk)
            rcc.fill(["shelf_quartz", "bamboo", "crate"])
            neo_roof(d, c, "garden")
        else:
            neo_roof(d, c, "solar")
        # tower crane in the yard
        mx, mz = 19, 22
        for y in range(y0, 20):
            d.set(mx, y, mz, "yellow_concrete" if y % 2 == 0 else "yellow_stained_glass")
        for x in range(12, 32):
            d.set(x, 20, mz, "yellow_concrete" if x in (12, 19, 31) else "iron_bars")
        d.set(mx, 21, mz, "yellow_concrete")
        d.set(mx - 1, 19, mz, "light_gray_stained_glass")
        for x in (17, 18):
            d.set(x, 19, mz, "gray_concrete") if x == 17 else None
        for y in range(14, 20):
            d.set(26, y, mz, CHAIN)
        d.set(26, 13, mz, "stone_bricks")
    # yard: paving, stacks
    if L >= 3:
        for x in range(18, 35):
            for z in range(17, 29):
                if d.get(x, 1, z) == "minecraft:smooth_stone":
                    d.set(x, 1, z, "gray_concrete" if (x + z) % 7 else "yellow_concrete")
        for x, z, b, h in ((22, 19, "stone_bricks", 2), (23, 19, "stone_bricks", 1), (22, 20, "bricks", 2),
                           (29, 19, "white_concrete", 2), (30, 19, "white_concrete", 1), (29, 20, "glass", 1)):
            for k in range(h):
                d.set(x, y0 + k, z, b)
        log_pile(d, 24, 25, 28, 26, y0, 2, "birch_log", "x")
        for x in (21, 33):
            lamp_post(d, x, 27, y0, P)
    if L >= 5:                                                       # site gatehouse kiosk at the yard entrance
        k = build(d, 28, 19, 33, 25, 1, roof="flat")
        k.door(30, 19, "north")
        rk = k.room(0)
        rk.chairs_desk(1, "birch", top=sl("smooth_quartz", "top"), sit=False)
        rk.fill(["shelf_quartz", "bamboo", "crate"])
        neo_roof(d, k, "garden")
        for z in range(17, 29, 3):
            lamp_post(d, 34, z, y0, P)
        for x in (20, 23):
            d.set(x, y0, 28, "moss_block")
            tree(d, x, 28, y0 + 1, "birch", 3, 1)
    # top up seats with a bench by the door
    if seats < BSEATS[L]:
        bench(d, 12, 1, y0, "north", BSEATS[L] - seats, "birch")
    for rr in ([r0] + ([r1] if sto >= 2 else [])):
        pass
    return d


def builder_hw(rel, L):
    d = Design("Hearthwood", rel, (34, 24, 30), paving="gravel")
    P, y0 = "Hearthwood", 2
    sto = 1 if L == 1 else 2
    a = build(d, 3, 3, 17, 13, sto, roof="gable", axis="x", core=(15, 5) if sto > 1 else None,
              chimney=(4, 9, "east"))
    a.door(9, 3, "north")
    d.hut(4, y0, 4)
    d.sign(10, 4, 2, "north", ["Master Builder", "& Mason"], "dark_oak")
    r0 = a.room(0)
    r0.item("cartography_table", sides=("north", "east"))
    r0.item("crafting_table", sides=("north", "east"))
    r0.item("barrel", 2, sides=("south",))
    racks = r0.racks(BRACKS[L] if L <= 2 else 9, sides=("south",))
    if L >= 2:
        for it in ("smithing_table", "anvil", "grindstone", "stonecutter"):
            r0.item(it, sides=("south", "east", "north"))
        if L <= 3:
            r0.item("hopper", sides=("south", "east", "north"))
    if L >= 5:
        r0.item("ender_chest", sides=("south", "east", "north", "west"))
    r0.chairs_desk(2, "dark_oak")
    r0.rug(RUG[P])
    r0.fill(PACK_DECOR[P])
    r0.lights()
    seats = 2
    if sto >= 2:
        r1 = a.room(1)
        r1.books(12, sides=("south", "west"))
        r1.item("lectern", sides=("north", "east", "south"))
        r1.item("cartography_table", sides=("north", "east", "south"))
        r1.item("crafting_table", sides=("north", "east", "south"))
        seats += r1.chairs_desk(2, "dark_oak")
        if L >= 4:
            r1.bed("dark_oak", sides=("north", "east", "south"))
            r1.item("jukebox", sides=("north", "east", "south"))
        r1.fill(PACK_DECOR[P])
        r1.lights()
    # yard walls and gate
    for x in range(16, 33):
        d.set(x, y0, 12, "cobblestone_wall") if L < 3 else None
    flower_bed(d, 3, 1, 6, 1, y0, seed=1)
    flower_bed(d, 11, 1, 14, 1, y0, seed=2)
    lamp_post(d, 9, 1, y0, P) if False else None
    # ---- store barn with rack bays (L3+), loft at L5
    if L >= 3:
        bs = 2 if L >= 4 else 1
        bb = build(d, 19, 3, 29, 19, bs, H=5 if bs == 1 else 4, roof="gable", axis="z",
                   core=(27, 12) if bs > 1 else None)
        bb.opening(19, 8, 19, 10, 3, lg("stripped_dark_oak_log", "z"))
        bb.door(24, 3, "north")
        rb = bb.room(0)
        need = BRACKS[L] - racks - (0 if L < 4 else 0)
        racks += rb.racks(need if L < 5 else 30, sides=("east", "south", "north", "west"))
        rb.center_line([lg("oak_log", "z")] * 3 + ["stonecutter[facing=west]" if False else lg("oak_log", "z")], "z")
        rb.fill(["planks", "stone", "logs", "keg"])
        rb.lights()
        if bs > 1:
            rl = bb.room(1)
            racks += rl.racks(BRACKS[L] - racks, sides=("west", "north", "south"))
            rl.fill(["sack", "planks", "crate"])
            rl.lights()
        d.sign(23, 6, 2, "north", ["Timber", "& Stone Store"], "dark_oak")
    # ---- mason's lodge (L4+), upper floor at L5
    if L >= 4:
        cs = 2
        c = build(d, 3, 17, 15, 25, cs, roof="gable", axis="x", core=(4, 19) if cs > 1 else None,
                  chimney=(14, 21, "west"))
        c.door(9, 17, "north", double=True)
        rc = c.room(0)
        rc.item("domum_ornamentum:architectscutter", sides=("south", "west"))
        if racks < BRACKS[L]:
            racks += rc.racks(BRACKS[L] - racks, sides=("south",))
        rc.center_line(["stone_bricks", "chiseled_stone_bricks", sl("stone_brick", "top"), "stone_bricks"])
        rc.fill(["stone", "shelf_dark", "keg", "stone"])
        rc.lights()
        seats += rc.table_group("dark_oak", 4, "post", rug="brown_carpet")
        if L >= 4:
            ru = c.room(1)
            ru.bed("dark_oak", sides=("south",)) if False else None
            ru.table_group("oak", 4, "post", rug="red_carpet", sit=False)
            ru.books(6, sides=("south",))
            ru.fill(["shelf_dark", "plant", "wardrobe"])
            ru.lights()
    if L >= 5:                                                       # guild hall closing the yard
        g = build(d, 19, 21, 31, 28, 2, roof="gable", axis="x", core=(29, 22), chimney=(20, 25, "east"))
        g.door(24, 21, "north", double=True)
        rg0 = g.room(0)
        for x in range(22, 28):
            d.set(x, rg0.y, 25, sl("dark_oak", "top"))
            d.chair(x, rg0.y, 24, "north", "dark_oak", sit=False)
            d.chair(x, rg0.y, 26, "south", "dark_oak", sit=False)
            rg0.used.update({(x, 24), (x, 25), (x, 26)})
        rg0.fill(["shelf_dark", "banner_red", "keg", "plant"])
        rg0.lights()
        rg1 = g.room(1)
        rg1.books(10, sides=("south", "east"))
        rg1.table_group("dark_oak", 4, "post", rug="red_carpet", sit=False)
        rg1.fill(["chisel", "plant", "shelf_dark"])
        rg1.lights()
        d.sign(26, 5, 20, "north", ["Builders'", "Guild"], "dark_oak")
        for x in range(16, 33):
            if d.air(x, y0, 29):
                d.set(x, y0, 29, "cobblestone_wall")
    # yard: stacks, saw horse, hoist, water butt, bench
    yz = 13
    log_pile(d, 17, 22, 18, 27, y0, 2, "oak_log", "z") if L >= 3 else log_pile(d, 18, 5, 20, 9, y0, 2, "oak_log", "z")
    sawhorse(d, 8, 14, y0)
    d.set(12, y0, 14, "water_cauldron[level=3]")
    for x, z, b, h in ((4, 14, "stone_bricks", 2), (5, 14, "stone_bricks", 1), (4, 15, "cobblestone", 1)):
        for k in range(h):
            d.set(x, y0 + k, z, b)
    if seats < BSEATS[L]:
        bench(d, 11, 15 if L >= 4 else 14, y0, "south", BSEATS[L] - seats, "dark_oak") if L >= 4 else \
            bench(d, 10, 13, y0, "north", BSEATS[L] - seats, "dark_oak")
    tree(d, 31, 26, y0, "oak", 4, 2)
    tree(d, 31, 22, y0, "oak", 4, 2) if L >= 2 else None
    for x, z in ((17, 2), (30, 2)):
        lamp_post(d, x, z, y0, P)
    wagon(d, 22, 22, y0, "oak", "stone_bricks") if L >= 3 else None
    return d


def builder_cas(rel, L):
    d = Design("Cascadia", rel, (34, 24, 34), paving="coarse_dirt")
    P, y0 = "Cascadia", 2
    sto = 1 if L == 1 else 2
    a = build(d, 5, 4, 17, 12 if L == 1 else 16, sto, roof="gable", axis="z",
              core=(6, 9) if sto > 1 else None)
    mid = 11
    a.opening(mid - 1, 4, mid + 1, 4, 4 if sto == 1 else 3, lg("dark_oak_log", "x"))
    # hay-hoist beam
    d.set(mid, a.ridge - 2, 3, lg("dark_oak_log", "z"))
    d.set(mid, a.ridge - 2, 2, lg("dark_oak_log", "z"))
    for y in range(a.ridge - 5, a.ridge - 2):
        d.set(mid, y, 2, CHAIN)
    d.set(mid, a.ridge - 6, 2, "hay_block[axis=y]")
    d.sign(mid - 3, 5, 3, "north", ["TIMBER", "FRAMERS"], "spruce")
    d.hut(16, y0, 5)
    r0 = a.room(0)
    r0.item("crafting_table", sides=("east",))
    r0.item("cartography_table", sides=("east",))
    r0.item("barrel", 2, sides=("east",))
    racks = r0.racks(min(BRACKS[L], 12), sides=("west", "south"))
    if L >= 2:
        for it in ("smithing_table", "anvil", "grindstone", "stonecutter"):
            r0.item(it, sides=("east", "south"))
        if L <= 3:
            r0.item("hopper", sides=("east", "south"))
    seats = r0.chairs_desk(2, "spruce")
    sawhorse(d, 10, 10, y0, "spruce", "z")
    r0.fill(PACK_DECOR[P])
    r0.lights()
    if sto >= 2:
        r1 = a.room(1)
        r1.books(12, sides=("west", "south", "east"))
        r1.item("lectern", sides=("south", "east", "north"))
        r1.item("cartography_table", sides=("south", "east", "north"))
        r1.item("crafting_table", sides=("south", "east", "north"))
        seats += r1.chairs_desk(2, "spruce")
        r1.fill(PACK_DECOR[P])
        r1.lights()
    # front: bench, lamp, logs
    log_pile(d, 1, 6, 3, 14, y0, 3, "spruce_log", "z")
    lamp_post(d, 4, 2, y0, P)
    lamp_post(d, 18, 2, y0, P)
    # ---- covered porch across the barn front (L3+) and pole lumber shed
    if L >= 3:
        for x in range(4, 19):
            for z in (1, 2, 3):
                d.set(x, 1, z, "spruce_planks")
            d.set(x, 6, 0, st("dark_oak", "south"))
            for z in (1, 2, 3):
                d.set(x, 6, z, sl("dark_oak") if z < 3 else sl("dark_oak", "top"))
        for x in (4, 8, 14, 18):
            d.fill(x, y0, 1, x, 5, 1, lg("spruce_log", "y"))
        for x in range(5, 18):
            if x not in (8, 14) and not 10 <= x <= 12:
                d.set(x, y0, 1, "spruce_fence")
        d.set(11, 5, 2, LANT)
        crate_stack(d, 6, 2, y0, 2)
        sx1, sx2, sz1, sz2 = 20, 31, 4, 16
        for x, z in ring(sx1, sz1, sx2, sz2):
            if (x - sx1) % 4 == 0 and z in (sz1, sz2) or (z - sz1) % 4 == 0 and x in (sx1, sx2) or (x, z) in ((sx2, sz2),):
                for y in range(y0, 7):
                    d.set(x, y, z, lg("spruce_log", "y"))
                d.set(x, 1, z, "cobblestone")
        for x in range(sx1, sx2 + 1):
            for z in range(sz1, sz2 + 1):
                d.set(x, 1, z, "spruce_planks")
            d.set(x, 7, sz1, lg("stripped_spruce_log", "x"))
            d.set(x, 7, sz2, lg("stripped_spruce_log", "x"))
        for z in range(sz1, sz2 + 1):
            d.set(sx1, 7, z, lg("stripped_spruce_log", "z"))
            d.set(sx2, 7, z, lg("stripped_spruce_log", "z"))
        d.gable(sx1, sz1, sx2, sz2, 8, "x", "dark_oak_stairs", "dark_oak_slab", "spruce_planks")
        for z in range(sz1 + 2, sz2 - 1, 4):
            for x in range(sx1 + 1, sx2):
                d.set(x, 7, z, lg("stripped_spruce_log", "x"))
            d.set(25, 6, z, LANT)
        need = BRACKS[L] - racks
        n = 0
        for z in (sz2 - 1, sz2 - 2) if need > 0 else ():
            n += rack_line(d, [(x, z) for x in range(sx1 + 1, sx2)], y0, need - n)
        racks += n
        log_pile(d, sx1 + 1, sz1 + 1, sx2 - 1, sz1 + 2, y0, 2, "stripped_spruce_log", "x")
        log_pile(d, sx1 + 1, sz1 + 5, sx2 - 1, sz1 + 6, y0, 1, "spruce_log", "x")
        wagon(d, 26, 1, y0, "spruce", lg("spruce_log", "x"))
    # ---- bunk & plan cabin (L4+)
    if L >= 4:
        c = build(d, 5, 20, 15, 28, 2, roof="gable", axis="x", core=(13, 22), chimney=(6, 24, "east"))
        c.door(9, 20, "north")
        # porch
        for x in range(4, 17):
            for z in (17, 18, 19):
                d.set(x, 1, z, "spruce_planks")
        for x in (4, 16):
            d.fill(x, y0, 17, x, 5, 17, lg("spruce_log", "y"))
        for x in range(3, 18):
            d.set(x, 6, 16, st("dark_oak", "south"))
            for z in (17, 18, 19):
                d.set(x, 6, z, sl("dark_oak"))
        rc = c.room(0)
        rc.item("domum_ornamentum:architectscutter", sides=("south", "east"))
        rc.item("jukebox", sides=("south", "east"))
        if L >= 5:
            rc.item("ender_chest", sides=("south", "east"))
        seats += rc.table_group("spruce", 4, "post", rug="green_carpet")
        rc.fill(PACK_DECOR[P])
        rc.lights()
        ru = c.room(1)
        ru.bed("spruce", sides=("south", "west"))
        ru.bed("spruce", sides=("south", "west", "north"))
        ru.fill(["wardrobe", "shelf_spruce", "plant"])
        ru.lights()
        bench(d, 5, 18, y0, "south", 2, "spruce", sit=False)
    # ---- smithy lean-to and log yard (L5)
    if L >= 5:
        sm = build(d, 20, 20, 30, 28, 2, roof="gable", axis="z", core=(28, 22), chimney=(21, 25, "east"))
        sm.door(25, 20, "north", double=True)
        rs = sm.room(0)
        if racks < BRACKS[L]:
            racks += rs.racks(BRACKS[L] - racks, sides=("south", "east"))
        rs.center_line(["anvil[facing=north]", "spruce_planks", "grindstone[face=floor,facing=north]"])
        rs.fill(["keg", "planks", "logs"])
        rs.lights()
        rs2 = sm.room(1)
        rs2.table_group("spruce", 4, "post", sit=False)
        rs2.fill(["sack", "keg", "shelf_spruce"])
        rs2.lights()
        log_pile(d, 1, 20, 3, 31, y0, 3, "spruce_log", "z")
    if seats < BSEATS[L]:
        bench(d, 13, 2, y0, "north", BSEATS[L] - seats, "spruce")
    tree(d, 32, 32, y0, "spruce", 5, 2)
    tree(d, 1, 32, y0, "spruce", 5, 2) if L < 5 else None
    return d


@design("builder")
def builder(pack, rel, L):
    return {"Neoterra": builder_neo, "Hearthwood": builder_hw, "Cascadia": builder_cas}[pack](rel, L)
