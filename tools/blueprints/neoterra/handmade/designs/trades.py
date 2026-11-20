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
                     wood="birch", stair="smooth_quartz", glass="glass_pane", glass_up="glass_pane",
                     flatroof="smooth_quartz", parapet="white_concrete", coping="smooth_quartz", beam=None,
                     shutter="birch", accent="cyan_concrete", sill="smooth_quartz"),
    "Hearthwood": dict(wall="calcite", wall0="bricks", post="stripped_dark_oak_log[axis=y]", band="dark_oak_planks",
                       floor="oak_planks", ufloor="spruce_planks", plinth="stone_bricks", wood="dark_oak",
                       stair="dark_oak", glass="glass_pane", glass_up="glass_pane", beam="stripped_dark_oak_log",
                       roof=("deepslate_tile_stairs", "deepslate_tile_slab"), end="calcite", shutter="dark_oak",
                       accent="red_terracotta", flatroof="spruce_planks", parapet="bricks", coping="brick"),
    "Cascadia": dict(wall=None, wall0=None, logwall="stripped_spruce_log", post="spruce_log[axis=y]",
                     band="stripped_spruce_wood[axis=y]", beam="spruce_log", floor="spruce_planks",
                     ufloor="spruce_planks", plinth="cobblestone", wood="spruce", stair="spruce",
                     glass="glass_pane", glass_up="glass_pane", roof=("dark_oak_stairs", "dark_oak_slab"),
                     end="spruce_planks", shutter="spruce", accent="red_terracotta", flatroof="spruce_planks",
                     parapet="spruce_planks", coping="spruce"),
}

# each trade gets its own palette inside the pack family (roof, walls, timber, accents)
TYPE_STY = {
    ("Neoterra", "builder"): dict(band="yellow_terracotta", accent="yellow_concrete"),
    ("Neoterra", "sawmill"): dict(wall="light_gray_concrete", wall0="light_gray_concrete", post="gray_concrete",
                                  band="orange_terracotta", flatroof="cut_copper", parapet="mangrove_planks",
                                  coping="cut_copper", accent="orange_concrete", wood="mangrove"),
    ("Neoterra", "lumberjack"): dict(wall="birch_planks", wall0="birch_planks", post="white_concrete",
                                     band="lime_terracotta", parapet="white_concrete", accent="lime_concrete"),
    ("Neoterra", "fletcher"): dict(wall="light_gray_concrete", wall0="light_gray_concrete", post="white_concrete",
                                   band="magenta_terracotta", parapet="white_concrete", accent="magenta_concrete",
                                   flatroof="light_gray_concrete", coping="smooth_stone"),
    ("Neoterra", "warehouse"): dict(wall="light_gray_concrete", wall0="polished_deepslate", post="deepslate_tiles",
                                    band="yellow_concrete", parapet="polished_deepslate", coping="deepslate_tile",
                                    flatroof="light_gray_concrete", accent="yellow_concrete"),
    ("Neoterra", "deliveryman"): dict(wall="white_terracotta", wall0="white_terracotta", post="white_concrete",
                                      band="orange_concrete", accent="orange_concrete", parapet="white_concrete"),
    ("Neoterra", "composter"): dict(wall="cherry_planks", wall0="cherry_planks", post="white_concrete",
                                    band="lime_terracotta", wood="cherry", accent="lime_concrete",
                                    parapet="white_concrete"),
    ("Hearthwood", "builder"): dict(shutter="dark_oak"),
    ("Hearthwood", "sawmill"): dict(wall="smooth_sandstone", wall0="stone_bricks", post="stripped_oak_log[axis=y]",
                                    beam="stripped_oak_log", roof=("brick_stairs", "brick_slab"),
                                    end="smooth_sandstone", wood="oak", stair="oak", shutter="oak"),
    ("Hearthwood", "lumberjack"): dict(wall="white_terracotta", wall0="cobblestone", roof=("spruce_stairs", "spruce_slab"),
                                       end="white_terracotta", wood="spruce", shutter="spruce"),
    ("Hearthwood", "fletcher"): dict(wall="yellow_terracotta", wall0="bricks", post="stripped_oak_log[axis=y]",
                                     beam="stripped_oak_log", roof=("mud_brick_stairs", "mud_brick_slab"),
                                     end="yellow_terracotta", wood="oak", stair="oak", shutter="crimson"),
    ("Hearthwood", "warehouse"): dict(wall="smooth_sandstone", wall0="sandstone", post="sandstone",
                                      roof=("dark_prismarine_stairs", "dark_prismarine_slab"), end="smooth_sandstone",
                                      wood="spruce", stair="spruce", plinth="stone_bricks", beam="stripped_spruce_log"),
    ("Hearthwood", "deliveryman"): dict(wall="calcite", wall0="bricks", roof=("granite_stairs", "granite_slab"),
                                        shutter="warped", accent="blue_terracotta"),
    ("Hearthwood", "composter"): dict(wall="mud_bricks", wall0="mud_bricks", post="stripped_oak_log[axis=y]",
                                      beam="stripped_oak_log", roof=("dark_oak_stairs", "dark_oak_slab"),
                                      end="mud_bricks", wood="oak", shutter="oak"),
    ("Cascadia", "builder"): dict(roof=("cobbled_deepslate_stairs", "cobbled_deepslate_slab"), accent="red_terracotta"),
    ("Cascadia", "sawmill"): dict(wall="dark_oak_planks", wall0="dark_oak_planks", post="stripped_spruce_log[axis=y]",
                                  roof=("dark_prismarine_stairs", "dark_prismarine_slab"), accent="yellow_terracotta",
                                  end="dark_oak_planks"),
    ("Cascadia", "lumberjack"): dict(logwall="spruce_log", post="stripped_spruce_log[axis=y]",
                                     beam="stripped_spruce_log", roof=("mangrove_stairs", "mangrove_slab"),
                                     accent="green_terracotta"),
    ("Cascadia", "fletcher"): dict(wall="birch_planks", wall0="birch_planks", post="spruce_log[axis=y]",
                                   roof=("deepslate_tile_stairs", "deepslate_tile_slab"), end="birch_planks",
                                   accent="green_terracotta", shutter="dark_oak"),
    ("Cascadia", "warehouse"): dict(wall="mangrove_planks", wall0="mangrove_planks", post="spruce_log[axis=y]",
                                    roof=("cobbled_deepslate_stairs", "cobbled_deepslate_slab"), end="mangrove_planks",
                                    accent="yellow_terracotta"),
    ("Cascadia", "deliveryman"): dict(roof=("warped_stairs", "warped_slab"), accent="green_terracotta",
                                      shutter="dark_oak"),
    ("Cascadia", "composter"): dict(wall="mossy_cobblestone", wall0="mossy_cobblestone", post="spruce_log[axis=y]",
                                    accent="green_terracotta", end="spruce_planks"),
}


def sty(d):
    p = dict(STY[d.pack])
    p.update(TYPE_STY.get((d.pack, d.req.get("base", "")), {}))
    p.update(getattr(d, "sty_over", {}) or {})
    return p


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
        d, P = self.d, sty(self.d)
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
        d, P = self.d, sty(self.d)
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
    P = sty(d)
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
                if pk == "Cascadia" and not (wall or P["wall"]):
                    blk = lg(P["logwall"], ax)
                elif pk != "Neoterra":
                    blk = (wall0 or P["wall0"] or wall or P["wall"]) if (s == 0 and storeys > 1) else (wall or P["wall"])
                else:
                    blk = (wall0 or P["wall0"]) if s == 0 else (wall or P["wall"])
                d.set(x, y, z, blk)
            # posts / pilasters
            i = (x - x1) if z in (z1, z2) else (z - z1)
            step = {"Neoterra": 4, "Hearthwood": 3 if (s > 0 or storeys == 1) else 99, "Cascadia": 4}[pk]
            if (x, z) in corners or i % step == 0:
                for y in range(fy + 1, top + 1):
                    d.set(x, y, z, P["post"] if not (pk == "Hearthwood" and s == 0 and storeys > 1) else P["plinth"])
        if s == 0 and P["plinth"]:
            for x, z in rg:
                d.set(x, y0, z, P["plinth"] if (x * 7 + z * 3) % 5 else ("mossy_cobblestone" if pk == "Cascadia" else "andesite"))
        if s > 0:
            d.fill(x1 + 1, fy, z1 + 1, x2 - 1, fy, z2 - 1, P["ufloor"])
            for x, z in rg:
                if pk != "Neoterra":
                    d.set(x, fy, z, lg(P["beam"], "x" if z in (z1, z2) else "z"))
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
                            d.set(x + ox, fy + 1, z + oz, sl(P["sill"], "top"))
                    else:
                        if i % 3 != 1 or i >= len(cells) - 1:
                            continue
                        d.window(x, fy + 2, z, x, fy + 3 if H >= 4 else fy + 2, z, P["glass"])
                        ox, oz = D4[side]
                        out = (x + ox, z + oz)
                        if not d.bp.inside(out[0], fy + 1, out[1]):
                            continue
                        far = (out[0] + ox, out[1] + oz)
                        roomy = s > 0 or (d.bp.inside(far[0], fy + 1, far[1]) and d.air(far[0], fy + 1, far[1])
                                          and d.air(far[0], fy + 2, far[1]))
                        if pk == "Cascadia" and roomy:
                            for sd in (CW[side], OPP[CW[side]]):
                                sx_, sz_ = D4[sd]
                                for k in (2, 3):
                                    c = (x + ox + sx_, fy + k, z + oz + sz_)
                                    if H >= 4 and d.bp.inside(*c) and d.air(*c):
                                        d.set(*c, tr(P["shutter"], sd, "bottom", True))
                        if (s > 0 or side == "north") and roomy:
                            if d.air(out[0], fy + 1, out[1]) and d.air(out[0], fy + 2, out[1]):
                                d.set(out[0], fy + 1, out[1], tr(P["wood"], side, "top"))
                                d.set(out[0], fy + 2, out[1], "potted_" + FLOWERS[(x + z) % 6])
    # roof
    if roof == "flat":
        d.fill(x1, yr, z1, x2, yr, z2, P["flatroof"])
        for x, z in rg:
            d.set(x, yr + 1, z, P["parapet"])
            d.set(x, yr + 2, z, sl(P["coping"]))
        b.ridge = yr + 2
    elif roof == "gable":
        for x, z in rg:
            d.set(x, yr, z, lg(P["beam"], "x" if z in (z1, z2) else "z") if pk != "Neoterra" else P["post"])
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
                        d.set(x, y, z, lg(P["beam"], "y"))
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
                    d.set(x, yr, z, lg(P["beam"] if pk == "Hearthwood" else "stripped_spruce_log", "z"))
        else:
            for z in range(z1 + 2, z2 - 1, 4):
                for x in range(x1 + 1, x2):
                    d.set(x, yr, z, lg(P["beam"] if pk == "Hearthwood" else "stripped_spruce_log", "x"))
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

    def lane_ok(self, c, f):
        """The lane cell in front of a wall slot must stay walkable (else the slot is the only passage)."""
        lx, lz = c[0] + D4[f][0], c[1] + D4[f][1]
        d = self.d
        return d.air(lx, self.y, lz) and d.air(lx, self.y + 1, lz) and (lx, lz) not in self.used or \
            "carpet" in d.get(lx, self.y, lz)

    def slots(self, sides=("north", "east", "south", "west"), h=2):
        return [(c, f) for c, f in self.ring(sides) if self.free(*c, h=h) and self.lane_ok(c, f)]

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
            if not self.free(x, z) or not self.lane_ok((x, z), f):
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
    sto = 1 if L == 1 else 2 if L < 5 else 3
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
    if sto >= 3:                                                     # top floor: apprentices' dormitory
        r2 = a.room(2)
        for _ in range(3):
            r2.bed("oak", sides=("south", "north"))
        r2.table_group("oak", 4, "post", rug="orange_carpet", sit=False)
        r2.fill(["wardrobe", "shelf_dark", "plant"])
        r2.lights()
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
        g = build(d, 19, 21, 31, 28, 3, roof="gable", axis="x", core=(29, 23), chimney=(20, 25, "east"))
        g.door(24, 21, "north", double=True)
        rg0 = g.room(0)
        for x in range(22, 28):                                      # guild bench: long table facing the hearth
            d.set(x, rg0.y, 25, sl("dark_oak", "top"))
            d.chair(x, rg0.y, 24, "north", "dark_oak", sit=False)
            rg0.used.update({(x, 24), (x, 25)})
        rg0.fill(["shelf_dark", "banner_red", "keg", "plant"])
        rg0.lights()
        rg1 = g.room(1)
        rg1.books(10, sides=("south", "east"))
        rg1.table_group("dark_oak", 4, "post", rug="red_carpet", sit=False)
        rg1.fill(["chisel", "plant", "shelf_dark"])
        rg1.lights()
        rg2 = g.room(2)                                              # model & archive loft
        rg2.center_line(["oak_planks", sl("oak", "top"), "bricks", sl("oak", "top"), "stone_bricks"])
        rg2.fill(["crate", "sack", "shelf_dark", "chisel"])
        rg2.lights()
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
    if L >= 5:                                                       # open seasoning shed for oak beams
        for z in range(3, 20):
            for x in range(30, 34):
                d.set(x, 6, z, sl("brick", "bottom") if x > 31 else sl("brick", "top"))
            if z % 4 == 3:
                d.fill(33, y0, z, 33, 5, z, lg("stripped_dark_oak_log", "y"))
        log_pile(d, 31, 4, 32, 18, y0, 2, "dark_oak_log", "z")
        for z in range(5, 19, 4):
            d.set(32, 5, z, LANT)
        # front garden wall with piers, a well in the yard
        for x in range(2, 18):
            if 8 <= x <= 10:
                continue
            d.set(x, y0, 0, "bricks" if x % 4 == 2 else "brick_wall")
            if x % 4 == 2:
                d.set(x, y0 + 1, 0, sl("stone_brick"))
        flower_bed(d, 3, 1, 7, 1, y0, seed=4)
        flower_bed(d, 11, 1, 16, 1, y0, seed=5)
        wx, wz = 16, 15
        for x, z in ring(wx - 1, wz - 1, wx + 1, wz + 1):
            d.set(x, y0, z, "cobblestone" if (x + z) % 2 else "mossy_cobblestone")
        d.set(wx, y0, wz, "water_cauldron[level=3]")
        for x in (wx - 1, wx + 1):
            d.fill(x, y0 + 1, wz, x, y0 + 2, wz, "dark_oak_fence")
        for x in range(wx - 1, wx + 2):
            d.set(x, y0 + 3, wz, st("deepslate_tile", "south") if False else sl("deepslate_tile"))
        d.set(wx, y0 + 2, wz, CHAIN)
        hedge(d, [(0, z) for z in range(3, 29)] + [(x, 29) for x in range(0, 16)], y0, "oak")
        for z in (6, 14, 20, 26):
            lamp_post(d, 1, z, y0, P)
    if L < 5:
        tree(d, 31, 26, y0, "oak", 4, 2)
        tree(d, 31, 22, y0, "oak", 4, 2) if L >= 2 else None
    for x, z in ((17, 2), (30, 2)):
        lamp_post(d, x, z, y0, P)
    wagon(d, 31, 6, y0, "oak", "stone_bricks", "z") if L >= 3 else None
    return d


def builder_cas(rel, L):
    d = Design("Cascadia", rel, (34, 24, 34), paving="coarse_dirt")
    P, y0 = "Cascadia", 2
    sto = 1 if L == 1 else 2 if L < 5 else 3
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
    if sto >= 3:                                                     # hay & seasoning loft
        r2 = a.room(2)
        r2.fill(["hay", "logs", "sack", "planks"])
        r2.center_line([lg("stripped_spruce_log", "z")] * 6, "z")
        r2.lights()
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
        sx1, sx2, sz1, sz2 = 20, 31, 4, 18
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
        c = build(d, 5, 21, 15, 31, 2, roof="gable", axis="x", core=(13, 23), chimney=(6, 26, "east"))
        c.door(9, 21, "north")
        # porch
        for x in range(4, 17):
            for z in (18, 19, 20):
                d.set(x, 1, z, "spruce_planks")
        for x in (4, 16):
            d.fill(x, y0, 18, x, 5, 18, lg("spruce_log", "y"))
        for x in range(3, 18):
            d.set(x, 6, 17, st("dark_oak", "south"))
            for z in (18, 19, 20):
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
        bench(d, 5, 19, y0, "south", 2, "spruce", sit=False)
    # ---- smithy lean-to and log yard (L5)
    if L >= 5:
        sm = build(d, 20, 21, 30, 29, 2, roof="gable", axis="z", core=(28, 23), chimney=(21, 26, "east"))
        sm.door(25, 21, "north", double=True)
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
        for z in range(19, 33):                                      # split-rail fence round the log yard
            d.set(0, y0, z, "spruce_fence")
        for x in range(0, 5):
            d.set(x, y0, 32, "spruce_fence")
            d.set(x, y0, 19, "spruce_fence") if x != 2 else None
        for x in range(21, 30):                                      # smithy forecourt: lean-to canopy
            d.set(x, 6, 19, sl("dark_oak"))
            d.set(x, 6, 20, sl("dark_oak", "top"))
        d.set(23, 5, 20, LANT)
        crate_stack(d, 30, 20, y0, 2, LANT_S)
        d.set(30, y0, 19, "water_cauldron[level=3]")
        # water tower on timber legs
        for x, z in ((31, 30), (33, 30), (31, 32), (33, 32)):
            d.fill(x, y0, z, x, 9, z, lg("spruce_log", "y"))
        for x in range(31, 34):
            for z in range(30, 33):
                d.set(x, 10, z, "spruce_planks")
                for y in range(11, 15):
                    if (x, z) != (32, 31):
                        d.set(x, y, z, lg("stripped_spruce_log", "y") if y != 13 else "dark_oak_planks")
                    else:
                        d.set(x, y, z, "water_cauldron[level=3]" if y == 11 else "spruce_planks")
                d.set(x, 15, z, sl("dark_oak") if (x, z) != (32, 31) else "dark_oak_planks")
        d.set(32, 16, 31, sl("dark_oak"))
        # yard gate arch with the company sign, privy, rail fence along the street
        for x in (19, 32):
            d.fill(x, y0, 0, x, 7, 0, lg("spruce_log", "y"))
        for x in range(19, 33):
            d.set(x, 8, 0, lg("stripped_spruce_log", "x"))
        d.sign(25, 7, 1, "south", ["PINE RIDGE", "BUILDERS"], "spruce") if False else None
        d.sign(25, 8, 1, "south", ["PINE RIDGE", "BUILDERS"], "spruce")
        px, pz = 31, 25
        for x, z in ring(px, pz, px + 2, pz + 2):
            d.fill(x, y0, z, x, 4, z, "spruce_planks")
        d.door(32, y0, pz, "north", "spruce")
        d.set(32, 4, pz, "spruce_planks")
        for x in range(px, px + 3):
            for z in range(pz - 1, pz + 4):
                d.set(x, 5, z, sl("dark_oak"))
        d.set(32, 3, pz + 2, "spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]") if False else None
        wagon(d, 27, 31, y0, "spruce", "hay_block[axis=x]")
        for y in range(y0, 10):
            d.set(32, y, 30, "ladder[facing=south,waterlogged=false]") if False else None
    if seats < BSEATS[L]:
        bench(d, 13, 2, y0, "north", BSEATS[L] - seats, "spruce")
    tree(d, 32, 32, y0, "spruce", 5, 2)
    tree(d, 1, 32, y0, "spruce", 5, 2) if L < 5 else None
    return d


@design("builder")
def builder(pack, rel, L):
    return {"Neoterra": builder_neo, "Hearthwood": builder_hw, "Cascadia": builder_cas}[pack](rel, L)


# =============================================================================================== SAWMILL
"""
Sawmill
  Neoterra   "Timber processing plant" (copper roofs, light-grey + mangrove cladding, orange bands): north-light
             sawtooth saw hall with a straight saw line, lengthened at L2; glazed mill office (L3, 3 storeys at L5);
             lumber drying kiln with roof vents (L4); covered log yard with a gantry crane (L5).
  Hearthwood "Watermill" (sandstone & stone, oak framing, red clay-tile roofs): stone mill house over a mill race
             with an undershot water wheel and gear train, timber upper floor from L2; the sawyer's cottage (L3),
             a plank drying barn (L4), a cart shed and wheelwright's loft (L5).
  Cascadia   "Steam sawmill" (dark-oak siding, blue-green metal roofs, mustard trim): open pole saw shed with a
             log deck, longer at L2 with a teepee burner; false-front mill office (L3); planing mill (L4, 2
             storeys); bunkhouse and log flume (L5).
"""
SAWS = {1: 3, 2: 4, 3: 5, 4: 6, 5: 7}


def saw_line(d, cells, y, n, feed="stripped_birch_log", axis="x"):
    """Stonecutters (the saws) on consecutive cells with a log on the in-feed and out-feed end."""
    d.set(cells[0][0], y, cells[0][1], lg(feed, axis))
    for c in cells[1:n + 1]:
        d.item(c[0], y, c[1], "stonecutter", "north" if axis == "x" else "west")
    d.set(cells[n + 1][0], y, cells[n + 1][1], lg(feed, axis))


def sawtooth(d, b, glass="light_blue_stained_glass"):
    """North-light sawtooth roof on a flat roof: glazing rows with sloping quartz backs."""
    y = b.yr + 1
    for z in range(b.z1 + 1, b.z2):
        k = (z - b.z1) % 3
        for x in range(b.x1 + 1, b.x2):
            if k == 1:
                d.set(x, y, z, glass)
            elif k == 2:
                d.set(x, y, z, st("cut_copper", "north"))


def saw_neo(rel, L):
    d = Design("Neoterra", rel, (36, 18, 32), paving="smooth_stone")
    P, y0 = "Neoterra", 2
    x2 = 15 if L == 1 else 21
    a = build(d, 3, 4, x2, 13, 1, H=5, roof="flat")
    sawtooth(d, a)
    a.door(6, 4, "north", double=True)
    a.opening(x2, 8, x2, 10, 3, "orange_concrete")
    d.hut(4, y0, 5)
    d.sign(9, 5, 3, "north", ["NEOTERRA", "TIMBER WORKS"], "mangrove", glow=True, color="orange")
    ra = a.room(0)
    n = SAWS[L]
    saw_line(d, [(x, 9) for x in range(6, 6 + n + 2)], y0, n, "stripped_mangrove_log")
    for x in range(6, 8 + n):
        ra.used.update({(x, 9)})
    ra.item("crafting_table", sides=("west",))
    ra.racks(L, 1, sides=("south",))
    ra.fill(["planks", "logs", "crate", "shelf_quartz"], sides=("south", "north"))
    ra.lights()
    for x in range(6, 8 + n):
        d.set(x, 1, 8, "orange_concrete")
        d.set(x, 1, 10, "orange_concrete")
    # forecourt
    for x in (1, x2 + 2):
        d.set(x, y0, 3, "moss_block")
        tree(d, x, 3, y0 + 1, "birch", 3, 1)
    lamp_post(d, 13, 2, y0, P)
    # log yard behind the hall
    log_pile(d, 3, 16, 9, 18, y0, 2, "birch_log", "x")
    if L >= 2:
        log_pile(d, 11, 16, 18, 18, y0, 3, "spruce_log", "x")
        for z in range(15, 21):
            d.set(2, y0, z, "light_gray_concrete")
            d.set(2, y0 + 1, z, "glass_pane")
        wagon(d, 23, 14, y0, "mangrove", lg("birch_log", "x"))
        for x in (24, 30):
            lamp_post(d, x, 2, y0, P)
        bench(d, 17, 2, y0, "north", 2, "mangrove", sit=False)
        for z in range(3, 16):                                      # planter strip along the west wall
            d.set(1, y0, z, "moss_block")
            d.set(1, y0 + 1, z, "azalea" if z % 2 else "fern")
    # ---- mill office (L3+)
    if L >= 3:
        so = 3 if L >= 5 else 2
        b = build(d, 24, 4, 32, 12, so, roof="flat", core=(30, 6), street_glass=True)
        b.door(26, 4, "north")
        rb = b.room(0)
        rb.item("lectern", sides=("west", "south"))
        rb.item("cartography_table", sides=("west", "south"))
        rb.chairs_desk(2, "mangrove", top=sl("smooth_quartz", "top"), sit=False)
        rb.fill(["shelf_quartz", "bamboo", "crate"])
        rr = b.room(1)
        rr.table_group("mangrove", 4, "slab", rug="orange_carpet", sit=False)
        for blk in ("smoker[facing=north,lit=false]", "water_cauldron[level=3]", sl("smooth_quartz", "top")):
            t = rr.take(("south",))
            if t:
                d.set(t[0][0], rr.y, t[0][1], blk)
        rr.fill(["shelf_quartz", "bamboo", "banner_cyan"])
        if so >= 3:
            r3 = b.room(2)
            r3.chairs_desk(3, "mangrove", top=sl("smooth_quartz", "top"), sit=False)
            r3.books(6, sides=("west",))
            r3.fill(["shelf_quartz", "bamboo"])
            neo_roof(d, b, "garden")
        else:
            neo_roof(d, b, "solar")
        bench(d, 28, 2, y0, "north", 2, "mangrove", sit=False)
    # ---- drying kiln (L4+)
    if L >= 4:
        k = build(d, 21, 16, 32, 25, 2 if L == 4 else 3, roof="flat", core=(22, 18))
        k.door(27, 16, "north", double=True)
        rk = k.room(0)
        rk.item("domum_ornamentum:architectscutter", sides=("east", "south"))
        rk.fill(["planks", "planks", "logs"])
        rk.center_line([lg("stripped_birch_log", "x")] * 5)
        rk2 = k.room(1)
        rk2.fill(["planks", "logs", "crate"])
        rk2.center_line(["birch_planks", "birch_planks", "birch_planks", "birch_planks"])
        if L >= 5:
            rk3 = k.room(2)
            rk3.fill(["planks", "logs"])
            rk3.center_line([lg("stripped_mangrove_log", "x")] * 5)
        for x in range(23, 31, 3):                                    # roof vents
            d.set(x, k.yr + 1, 20, "campfire[facing=north,lit=false,signal_fire=false,waterlogged=false]")
            d.set(x, k.yr + 1, 22, tr("iron", "north", "bottom"))
    # ---- covered log yard with gantry crane (L5)
    if L >= 5:
        for x in (2, 19):
            for z in (15, 27):
                d.fill(x, y0, z, x, 9, z, "gray_concrete")
        for x in range(2, 20):
            d.set(x, 10, 15, "orange_concrete")
            d.set(x, 10, 27, "orange_concrete")
            for z in range(15, 28):
                if x in (2, 19) or z % 4 == 3:
                    d.set(x, 10, z, "orange_concrete" if x in (2, 19) else "iron_bars")
        for x in range(1, 21):
            for z in range(14, 29):
                if z % 2 == 0:
                    d.set(x, 11, z, sl("cut_copper"))
        for y in range(6, 10):
            d.set(10, y, 21, CHAIN)
        d.set(10, 5, 21, lg("birch_log", "x"))
        log_pile(d, 3, 21, 9, 25, y0, 3, "birch_log", "x")
        log_pile(d, 11, 21, 18, 25, y0, 2, "dark_oak_log", "x")
        for z in (28, 31):
            for x in (24, 30):
                d.set(x, y0, z, "moss_block")
                tree(d, x, z, y0 + 1, "birch", 3, 1)
        for x in (21, 27, 33):
            lamp_post(d, x, 27, y0, P)
    return d


def water_wheel(d, x, wy, wc, r=3, wood="dark_oak"):
    """Undershot wheel in the plane x (axle along x): rim of planks/logs, spokes, hub."""
    for dy in range(-r, r + 1):
        for dz in range(-r, r + 1):
            rr = (dy * dy + dz * dz) ** 0.5
            if r - 0.5 <= rr < r + 0.6:
                d.set(x, wy + dy, wc + dz, f"{wood}_planks" if (dy + dz) % 2 else lg(f"stripped_{wood}_log", "x"))
            elif rr < r - 0.5 and (dy == 0 or dz == 0):
                d.set(x, wy + dy, wc + dz, lg("stripped_spruce_log", "x" if (dy, dz) == (0, 0) else
                                              "y" if dz == 0 else "z"))


def saw_hw(rel, L):
    d = Design("Hearthwood", rel, (33, 22, 30), paving="gravel")
    P, y0 = "Hearthwood", 2
    sto = {1: 1, 2: 2, 3: 2, 4: 2, 5: 3}[L]
    z2 = 12 if L == 1 else 15
    a = build(d, 4, 4, 14, z2, sto, roof="gable", axis="z", core=(12, 8) if sto > 1 else None)
    a.door(10, 4, "north")
    d.hut(5, y0, 5)
    d.sign(11, 4, 3, "north", ["Wheelwright", "Saw Mill"], "oak")
    # mill race, wheel, axle and gear train
    for z in range(0, 30):
        d.set(16, 1, z, "water[level=0]")
        d.set(17, 1, z, "water[level=0]")
        d.set(15, 1, z, "stone_bricks")
        d.set(18, 1, z, "stone_bricks")
        if z not in (1, 2):
            d.set(18, y0, z, "stone_brick_wall")
    for x in (16, 17):
        d.set(x, y0, 2, sl("oak"))
        d.set(x, y0, 1, sl("oak"))
    water_wheel(d, 16, 4, 9, 3 if L < 3 else 3)
    if L >= 3:
        water_wheel(d, 17, 4, 9, 3)
    for x in (14, 15):
        d.set(x, 4, 9, lg("dark_oak_log", "x"))
    ra = a.room(0)
    n = SAWS[L]
    saw_line(d, [(8, z) for z in range(5, 5 + n + 2)], y0, n, "stripped_oak_log", "z")
    ra.used.update({(8, z) for z in range(5, 7 + n)})
    d.set(13, y0, 9, "grindstone[face=floor,facing=east]")       # gear train
    d.fill(13, y0 + 1, 9, 13, 3, 9, lg("dark_oak_log", "y"))
    d.set(13, 4, 9, lg("dark_oak_log", "x"))
    ra.used.add((13, 9))
    ra.item("crafting_table", sides=("west",))
    ra.racks(min(L, 3), 1, sides=("west", "south"))
    ra.fill(["logs", "planks", "keg", "shelf_oak"])
    ra.lights()
    racks = min(L, 3)
    if sto >= 2:
        r1 = a.room(1)
        racks += r1.racks(L - racks, 1, sides=("west", "south"))
        r1.fill(["sack", "planks", "logs", "crate"])
        r1.center_line([lg("stripped_oak_log", "z")] * 4, "z")
        r1.lights()
    if sto >= 3:
        r2 = a.room(2)
        r2.fill(["sack", "hay", "crate"])
        r2.lights()
    log_pile(d, 4, z2 + 3, 12, z2 + 4, y0, 2, "oak_log", "x")
    flower_bed(d, 5, 1, 8, 2, y0, seed=3)
    lamp_post(d, 12, 1, y0, P)
    # ---- sawyer's cottage (L3+)
    if L >= 3:
        d.sty_over = dict(wall="calcite", wall0="bricks", post="stripped_dark_oak_log[axis=y]",
                          beam="stripped_dark_oak_log", end="calcite")
        b = build(d, 20, 4, 30, 11, 2 if L < 5 else 3, roof="gable", axis="x", core=(28, 6), chimney=(21, 8, "east"))
        d.sty_over = {}
        b.door(24, 4, "north")
        rb = b.room(0)
        rb.item("lectern", sides=("south", "east"))
        rb.item("cartography_table", sides=("south", "east"))
        rb.chairs_desk(2, "oak", sit=False)
        rb.rug(RUG[P])
        rb.fill(["shelf_dark", "plant", "keg"])
        rb.lights()
        rb1 = b.room(1)
        rb1.bed("oak", sides=("south", "north"))
        rb1.bed("oak", sides=("south", "north"))
        rb1.fill(["wardrobe", "shelf_dark", "plant"])
        rb1.lights()
        if L >= 5:
            rb2 = b.room(2)
            rb2.bed("oak", sides=("south", "north"))
            rb2.table_group("oak", 4, "post", rug="orange_carpet", sit=False)
            rb2.fill(["shelf_dark", "plant", "sack"])
            rb2.lights()
        for x in range(20, 31):
            if x not in (24,):
                d.set(x, y0, 2, "oak_fence")
        flower_bed(d, 21, 3, 22, 3, y0, seed=2) if False else None
        tree(d, 32, 3, y0, "oak", 4, 1)
    # ---- plank drying barn (L4+), wheelwright & cart shed (L5)
    if L >= 4:
        c = build(d, 20, 15, 30, 25, 2, roof="gable", axis="z", core=(28, 17))
        c.opening(24, 15, 26, 15, 3, lg("stripped_oak_log", "x"))
        rc = c.room(0)
        rc.item("domum_ornamentum:architectscutter", sides=("west",))
        for z in (16, 20, 24):
            lamp_post(d, 32, z, y0, P)
        rc.fill(["planks", "planks", "logs"])
        rc.center_line([lg("stripped_oak_log", "z")] * 6, "z")
        rc.lights()
        if L >= 4:
            rc2 = c.room(1)
            rc2.fill(["planks", "sack", "planks"])
            rc2.center_line(["oak_planks"] * 5, "z")
            rc2.lights()
    if L >= 5:
        e = build(d, 3, 19, 13, 27, 2, roof="gable", axis="x", core=(4, 21))
        e.opening(7, 19, 9, 19, 3, lg("stripped_oak_log", "x"))
        re = e.room(0)
        wagon(d, 8, 24, y0, "oak", "oak_planks")
        re.used.update({(x, 24) for x in range(7, 11)})
        re.fill(["logs", "keg", "planks"])
        re.lights()
        re2 = e.room(1)
        re2.center_line(["anvil[facing=north]", "oak_planks", "grindstone[face=floor,facing=north]"])
        re2.fill(["logs", "shelf_oak", "crate"])
        re2.lights()
    return d


def saw_cas(rel, L):
    d = Design("Cascadia", rel, (34, 22, 40), paving="coarse_dirt")
    P, y0 = "Cascadia", 2
    x1, z1, z2 = 4, 7, 14
    x2 = 15 if L == 1 else 22
    d.fill(x1, 1, z1, x2, 1, z2, "spruce_planks")
    for x, z in ring(x1, z1, x2, z2):
        if (z in (z1, z2) and ((x - x1) % 4 == 0 or x == x2)) or (x in (x1, x2) and z in (z1, z2)):
            d.fill(x, y0, z, x, 5, z, lg("spruce_log", "y"))
            d.set(x, 1, z, "cobblestone")
        elif z == z2 or (x == x2 and z > z1):
            d.fill(x, y0, z, x, 3, z, "dark_oak_planks")
            d.set(x, 4, z, tr("spruce", "north" if z == z2 else "east", "bottom"))
    for x in range(x1, x2 + 1):
        d.set(x, 6, z1, lg("stripped_spruce_log", "x"))
        d.set(x, 6, z2, lg("stripped_spruce_log", "x"))
    for z in range(z1, z2 + 1):
        d.set(x1, 6, z, lg("stripped_spruce_log", "z"))
        d.set(x2, 6, z, lg("stripped_spruce_log", "z"))
    for x in range(x1 + 4, x2, 4):
        for z in range(z1 + 1, z2):
            d.set(x, 6, z, lg("stripped_spruce_log", "z"))
        d.set(x, 5, 10, LANT)
    d.gable(x1, z1, x2, z2, 7, "x", "dark_prismarine_stairs", "dark_prismarine_slab", "dark_oak_planks")
    for x in range(x1, x2 + 1):
        d.set(x, 6, z1 - 1, "yellow_terracotta") if False else None
    n = SAWS[L]
    saw_line(d, [(x, 10) for x in range(x1 + 3, x1 + 5 + n)], y0, n, "stripped_spruce_log", "x")
    d.hut(x1 + 1, y0, z1 + 1)
    d.item(x1 + 2, y0, z2 - 1, "crafting_table")
    rack_line(d, [(x, z2 - 1) for x in range(x1 + 4, x2, 2)], y0, L, 1, "north")
    for x in range(x1 + 5, x2, 2):
        if d.air(x, y0, z2 - 1):
            d.set(x, y0, z2 - 1, "spruce_planks")
            d.set(x, y0 + 1, z2 - 1, sl("spruce"))
    log_pile(d, 0, z1 + 1, 2, z2 - 1, y0, 2, "spruce_log", "z")
    for x in range(x1 + 2, x1 + 6):
        d.set(x, y0, z1 - 2, "stripped_spruce_wood[axis=x]")
    lamp_post(d, x1 - 1, 4, y0, P)
    # ---- teepee burner (L2+)
    if L >= 2:
        cx, cz = 29, 17
        for y in range(y0, 13):
            rr = 3 if y < 6 else 2 if y < 9 else 1 if y < 12 else 0
            for dx in range(-3, 4):
                for dz in range(-3, 4):
                    dist = (dx * dx + dz * dz) ** 0.5
                    if rr - 0.5 <= dist < rr + 0.5 or (rr == 0 and dist < 0.5):
                        b_ = "iron_bars" if y >= 11 else ("weathered_cut_copper" if (y + dx) % 3 else "exposed_cut_copper")
                        d.set(cx + dx, y, cz + dz, b_)
        for k in (0, 1):
            d.set(cx, y0 + k, cz - 3, AIR)
        d.set(cx, y0, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        for z in range(z1 + 4, cz - 3):                               # sawdust conveyor on trestles
            d.set(24, 4, z, "smooth_stone_slab[type=bottom,waterlogged=false]")
        log_pile(d, 1, 17, 8, 19, y0, 3, "spruce_log", "x")
    # ---- false-front mill office (L3+)
    if L >= 3:
        b = build(d, 25, 2, 31, 9, 2, roof="gable", axis="z", core=(28, 4))
        for x in range(24, 33):
            for y in range(y0, b.ridge + 2):
                if y >= b.yr or x in (24, 32):
                    d.set(x, y, 1, "dark_oak_planks" if x not in (24, 32) else lg("spruce_log", "y"))
            d.set(x, b.ridge + 2, 1, sl("dark_oak"))
            d.set(x, b.yr, 1, "yellow_terracotta")
        b.door(26, 2, "north")
        d.set(26, y0, 1, AIR)
        d.set(26, y0 + 1, 1, AIR)
        d.sign(28, b.ridge, 0, "north", ["MILL", "OFFICE"], "spruce")
        rb = b.room(0)
        rb.item("lectern", sides=("west", "south"))
        rb.item("cartography_table", sides=("west", "south"))
        rb.fill(["shelf_spruce", "keg", "plant"])
        rb.lights()
        rb1 = b.room(1)
        rb1.chairs_desk(2, "spruce", sit=False)
        rb1.fill(["shelf_spruce", "chisel", "plant"])
        rb1.lights()
    # ---- planing mill (L4+)
    if L >= 4:
        c = build(d, 4, 21, 16, 29, 2, roof="gable", axis="x", core=(14, 23))
        c.opening(8, 21, 10, 21, 3, lg("spruce_log", "x"))
        rc = c.room(0)
        rc.item("domum_ornamentum:architectscutter", sides=("west", "south"))
        rc.center_line(["spruce_planks", "stonecutter[facing=north]" if False else lg("stripped_spruce_log", "x"),
                        "grindstone[face=floor,facing=north]", lg("stripped_spruce_log", "x"), "spruce_planks"])
        rc.fill(["planks", "planks", "logs", "keg"])
        rc.lights()
        rc2 = c.room(1)
        rc2.fill(["planks", "sack", "planks", "crate"])
        rc2.center_line(["spruce_planks"] * 6)
        rc2.lights()
    # ---- bunkhouse and log flume (L5)
    if L >= 5:
        e = build(d, 19, 22, 25, 31, 2, roof="gable", axis="z", core=(20, 24), chimney=(24, 28, "west"))
        e.door(22, 22, "north")
        re = e.room(0)
        re.table_group("spruce", 4, "post", sit=False) or re.chairs_desk(2, "spruce", sit=False)
        re.fill(["keg", "shelf_spruce", "plant"])
        re.lights()
        re2 = e.room(1)
        for _ in range(3):
            re2.bed("spruce", sides=("east", "west", "south"))
        re2.fill(["wardrobe", "plant"])
        re2.lights()
        for x in range(27, 34):                                         # flume on trestles
            for z in (26, 27):
                d.set(x, 5, z, "spruce_planks" if z == 26 else "water_cauldron[level=3]")
            if x % 3 == 0:
                d.fill(x, y0, 26, x, 4, 26, "spruce_fence")
        log_pile(d, 27, 28, 33, 31, y0, 2, "spruce_log", "x")
        # open lumber shed with graded stacks
        lx1, lz1, lx2, lz2 = 3, 32, 25, 38
        for x, z in ring(lx1, lz1, lx2, lz2):
            if (x - lx1) % 4 == 0 and z in (lz1, lz2) or x in (lx1, lx2) and z in (lz1, lz2):
                d.fill(x, y0, z, x, 5, z, lg("spruce_log", "y"))
                d.set(x, 1, z, "cobblestone")
        for x in range(lx1, lx2 + 1):
            d.set(x, 6, lz1, lg("stripped_spruce_log", "x"))
            d.set(x, 6, lz2, lg("stripped_spruce_log", "x"))
        d.gable(lx1, lz1, lx2, lz2, 7, "x", "dark_prismarine_stairs", "dark_prismarine_slab", "dark_oak_planks")
        for x in range(lx1 + 1, lx2, 3):
            for z in (lz1 + 1, lz1 + 2, lz2 - 2, lz2 - 1):
                for k in range(3 if z in (lz1 + 1, lz2 - 1) else 2):
                    d.set(x, y0 + k, z, "spruce_planks" if k % 2 == 0 else "stripped_spruce_wood[axis=x]")
                    d.set(x + 1, y0 + k, z, "dark_oak_planks" if k % 2 == 0 else "stripped_spruce_wood[axis=x]")
        for x in range(lx1 + 2, lx2, 4):
            d.set(x, 6, 35, lg("stripped_spruce_log", "z")) if False else None
            d.set(x, 6, 35, LANT) if False else None
    return d


@design("sawmill")
def sawmill(pack, rel, L):
    return {"Neoterra": saw_neo, "Hearthwood": saw_hw, "Cascadia": saw_cas}[pack](rel, L)
