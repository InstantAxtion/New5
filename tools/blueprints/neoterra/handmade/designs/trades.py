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


def spot_trees(d, cells, kind="oak", h=4, r=1):
    """Trees at the hand-picked ground cells."""
    for x, z in cells:
        tree(d, x, z, d.gy + 1, kind, h, r)


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

    def room(self, s, x1=None, z1=None, x2=None, z2=None, back="south"):
        return (self.x1 + 1, self.z1 + 1, self.x2 - 1, self.z2 - 1, self.stand(s))

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
                    else:
                        if i % 3 != 1 or i >= len(cells) - 1:
                            continue
                        d.window(x, fy + 2, z, x, fy + 3 if H >= 4 else fy + 2, z, P["glass"])
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
            lo_, hi_ = (z1, z2) if axis == "x" else (x1, x2)
            for x, z in ends_cells:
                c = z if axis == "x" else x
                top_ = yr + 1 + min(c - lo_, hi_ - c)               # height of the gable triangle here
                for y in range(yr + 1, top_):
                    if pk == "Hearthwood" and (c - mid) % 2 == 0:
                        d.set(x, y, z, lg(P["beam"], "y"))
                    elif pk == "Cascadia" and c % 2 == 0:
                        d.set(x, y, z, lg("stripped_spruce_log", "y"))
            # attic vent window
            for e in ((x1, mid) if axis == "x" else (mid, z1), (x2, mid) if axis == "x" else (mid, z2)):
                yv = b.ridge - 2
                if yv > yr + 1:
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


def neo_roof(d, b, lines):
    """Roof-top features on a flat Neoterra roof, as explicit lines (x1, x2, z, block[, h]) chosen per building:
    solar panel rows (daylight detectors), planter rows (moss/azalea), plant units (iron block + vent)."""
    y = b.yr + 1
    for ln in lines:
        x1, x2, z, blk = ln[:4]
        for x in range(x1, x2 + 1):
            d.set(x, y, z, blk)
            if len(ln) > 4:
                d.set(x, y + 1, z, ln[4])


SOLAR = "daylight_detector[inverted=false,power=0]"
MOSS = "moss_carpet"


# =============================================================================================== hand placement
def fit(d, y, spec, wood="oak"):
    """Place hand-chosen furniture at the given coordinates of one room (standing height y). Each entry:
      ("i", x, z, block, facing)   required work block      ("s", x, z, block)  block on the floor
      ("o", x, z, block)           block one up (on a desk)  ("c", x, z, back[, sit])  chair, backrest side
      ("r", x, z, h)               rack column               ("b", x, z, h, facing)  barrel column (counted)
      ("k", x, z, h)               bookshelf column          ("bed", x, z, facing[, colour])  head at x, z
      ("L", x, z)                  lantern hung from the ceiling above ("G", x, z, block) light set in the ceiling
      ("rug", x1, z1, x2, z2, colour)  carpet laid on the given rectangle
      ("st", x, z, facing)         decorative stairs (sofa end / step) without a seat tag"""
    seats = 0
    for e in spec:
        k = e[0]
        if k == "i":
            d.item(e[1], y, e[2], e[3], e[4] if len(e) > 4 else None)
        elif k == "s":
            d.set(e[1], y, e[2], e[3])
        elif k == "o":
            d.set(e[1], y + 1, e[2], e[3])
        elif k == "c":
            sit = e[4] if len(e) > 4 else True
            d.chair(e[1], y, e[2], e[3], wood, sit)
            seats += 1 if sit else 0
        elif k == "st":
            d.set(e[1], y, e[2], st(wood, e[3]))
        elif k == "r":
            rack_col(d, e[1], e[2], y, e[3])
        elif k == "b":
            for h in range(e[3]):
                d.item(e[1], y + h, e[2], "barrel", e[4])
        elif k == "k":
            d.bookshelf(e[1], y, e[2], e[3])
        elif k == "bed":
            d.bed(e[1], y, e[2], e[3], e[4] if len(e) > 4 else None)
        elif k == "L":
            x, z = e[1], e[2]
            top = y + 3
            while d.air(x, top, z) and top < y + 7:
                top += 1
            for yy in range(y + 3, top):
                d.set(x, yy, z, CHAIN)
            d.set(x, y + 2, z, LANT)
        elif k == "G":
            d.set(e[1], y + 3 if len(e) < 5 else e[4], e[2], e[3])
        elif k == "rug":
            for x in range(e[1], e[3] + 1):
                for z in range(e[2], e[4] + 1):
                    d.set(x, y, z, e[5])
        else:
            raise ValueError(e)
    return seats


def pot(i):
    return "potted_" + ("fern", "azalea_bush", "red_tulip", "bamboo", "oxeye_daisy", "cornflower")[i % 6]


def flower_box(d, x, y, z, facing, wood="oak", flower="red_tulip"):
    """Window box under the window at (x, y+1, z) on a wall facing `facing`: trapdoor shelf and a potted plant."""
    ox, oz = D4[facing]
    d.set(x + ox, y, z + oz, tr(wood, facing, "top"))
    d.set(x + ox, y + 1, z + oz, "potted_" + flower)


def shutter_pair(d, x, y, z, facing, wood="spruce", h=2):
    """Open shutters either side of the window at (x, y, z) in a wall facing `facing`."""
    ox, oz = D4[facing]
    for sd in (CW[facing], OPP[CW[facing]]):
        sx, sz = D4[sd]
        for k in range(h):
            d.set(x + ox + sx, y + k, z + oz + sz, tr(wood, sd, "bottom", True))


def furnish(*a, **k):          # TEMP
    return 0


def furnish_all(*a, **k):      # TEMP
    return None


WOOD = {"Neoterra": "birch", "Hearthwood": "dark_oak", "Cascadia": "spruce"}
RUG = {"Neoterra": ("light_gray_carpet", "cyan_carpet"), "Hearthwood": ("red_carpet", "orange_carpet"),
       "Cascadia": ("brown_carpet", "green_carpet")}


# =============================================================================================== materials by level
# Levels 1-3 build in common materials; from L4 the premium finishes (quartz, copper, prismarine slate, sea
# lanterns, blackstone) appear as the visible upgrade.
DEMOTE = (
    ("smooth_quartz_stairs", "polished_diorite_stairs"), ("smooth_quartz_slab", "polished_diorite_slab"),
    ("smooth_quartz", "polished_diorite"), ("quartz_stairs", "polished_diorite_stairs"),
    ("quartz_slab", "polished_diorite_slab"), ("quartz_block", "calcite"), ("quartz_pillar", "calcite"),
    ("weathered_cut_copper", "brown_terracotta"), ("exposed_cut_copper", "terracotta"),
    ("cut_copper_stairs", "polished_granite_stairs"), ("cut_copper_slab", "polished_granite_slab"),
    ("cut_copper", "polished_granite"),
    ("dark_prismarine_stairs", "deepslate_tile_stairs"), ("dark_prismarine_slab", "deepslate_tile_slab"),
    ("dark_prismarine", "deepslate_tiles"),
    ("sea_lantern", "glowstone"), ("pearlescent_froglight", "glowstone"),
    ("polished_blackstone_brick_wall", "andesite_wall"), ("polished_blackstone_bricks", "polished_andesite"),
    ("iron_block", "smooth_stone"),
)


def demote(d, L):
    if L > 3:
        return d
    g = d.bp.grid
    for y in range(len(g)):
        for z in range(len(g[y])):
            row = g[y][z]
            for x in range(len(row)):
                st0 = row[x]
                if st0 == AIR or not st0.startswith("minecraft:"):
                    continue
                name = st0.split("[")[0][10:]
                if name == "end_rod":
                    row[x] = "minecraft:lantern[hanging=%s,waterlogged=false]" % ("true" if "facing=down" in st0 else "false")
                    continue
                for a_, b_ in DEMOTE:
                    if name == a_:
                        props = st0[len("minecraft:" + name):]
                        keep = b_.endswith(("_stairs", "_slab", "_wall"))
                        row[x] = "minecraft:" + b_ + (props if keep else "")
                        break
    return d


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
    FL = "pearlescent_froglight[axis=y]"
    # ground floor: plan desk at the street window, bench run on the back wall, rack bay on the west wall
    bench_run = [("i", 5, 11, "crafting_table"), ("i", 6, 11, "barrel", "north"), ("i", 7, 11, "barrel", "north")]
    if L >= 2:
        bench_run += [("i", 8, 11, "smithing_table"), ("i", 9, 11, "anvil", "east"),
                      ("i", 10, 11, "grindstone", "north"), ("i", 11, 11, "stonecutter", "north")]
        bench_run += [("i", 12, 11, "hopper")] if L <= 3 else []
    if L >= 5:
        bench_run += [("i", 12, 11, "ender_chest", "north")]
    racks = BRACKS[L] if L <= 2 else 12
    rack_z = (7, 8, 9) if racks <= 9 else (6, 7, 8, 9)
    fit(d, y0, bench_run + [("r", 4, z, 3) for z in rack_z] + [
        ("s", 11, 5, sl("smooth_quartz", "top")), ("s", 12, 5, sl("smooth_quartz", "top")),
        ("c", 11, 6, "south"), ("c", 12, 6, "south"), ("o", 12, 5, "white_candle[candles=1,lit=false,waterlogged=false]"),
        ("i", 13, 5, "cartography_table"),
        ("s", 8, 8, sl("birch", "top")), ("s", 9, 8, lg("stripped_birch_log", "x")), ("s", 10, 8, sl("birch", "top")),
        ("o", 8, 8, "potted_bamboo"), ("rug", 6, 5, 9, 6, "light_gray_carpet"),
        ("s", 4, 11, pot(3)), ("s", 13, 11, "chest[facing=north,type=single,waterlogged=false]"),
        ("G", 6, 8, FL), ("G", 11, 8, FL)], "birch")
    if sto >= 2:                                                     # drafting library
        fit(d, 6, [("k", 4, z, 2) for z in range(5, 11)] + [
            ("i", 7, 11, "lectern", "north"), ("i", 8, 11, "cartography_table"), ("i", 9, 11, "crafting_table"),
            ("s", 7, 7, sl("birch", "top")), ("s", 8, 7, sl("birch", "top")), ("c", 7, 8, "south"), ("c", 8, 8, "south"),
            ("o", 7, 7, "white_candle[candles=2,lit=false,waterlogged=false]"),
            ("s", 11, 5, sl("birch", "top")), ("o", 11, 5, "potted_bamboo"), ("s", 4, 11, pot(0)),
            ("rug", 6, 9, 10, 9, "cyan_carpet"), ("G", 8, 6, FL), ("G", 11, 9, FL)], "birch")
    if sto >= 3:                                                     # staff lounge with the duty bed
        fit(d, 10, [("bed", 5, 11, "south", "white"), ("s", 6, 11, sl("birch", "top")),
                    ("o", 6, 11, "white_candle[candles=1,lit=false,waterlogged=false]"), ("i", 12, 11, "jukebox"),
                    ("rug", 7, 7, 10, 8, "light_gray_carpet"), ("s", 8, 7, sl("smooth_quartz", "top")),
                    ("s", 9, 7, sl("smooth_quartz", "top")), ("c", 7, 9, "south"), ("c", 8, 9, "south"),
                    ("c", 9, 9, "south"), ("c", 10, 9, "south"), ("s", 4, 4, pot(3)), ("s", 13, 4, pot(1)),
                    ("G", 8, 5, FL), ("G", 11, 9, FL)], "birch")
        if sto >= 4:                                                 # top: meeting room
            fit(d, 14, [("s", x, 7, sl("smooth_quartz", "top")) for x in range(7, 12)] +
                [("c", x, 6, "north", False) for x in range(7, 12)] + [("c", x, 8, "south", False) for x in range(7, 12)] +
                [("k", 4, z, 1) for z in range(5, 10)] + [("s", 4, 11, pot(3)), ("s", 13, 11, pot(0)),
                                                          ("G", 9, 7, "sea_lantern")], "birch")
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
        y1 = hb.stand(0)
        n = aisles(d, 21, 6, 29, 13, y1, min(need, 48 if L < 5 else 27))
        racks += n
        top = 6 if L < 5 else 5
        fit(d, y1, [("s", 21, 4, "stone_bricks"), ("o", 21, 4, "stone_bricks"), ("s", 22, 4, "bricks"),
                    ("s", 28, 4, "white_concrete"), ("o", 28, 4, "white_concrete"), ("s", 29, 4, "glass"),
                    ("s", 31, 8, lg("birch_log", "z")), ("s", 31, 9, lg("birch_log", "z")),
                    ("o", 31, 8, lg("birch_log", "z")), ("s", 31, 12, "chest[facing=west,type=single,waterlogged=false]"),
                    ("s", 32, 14, pot(3)), ("G", 25, 8, FL, top), ("G", 25, 12, FL, top), ("G", 31, 10, FL, top)])
        if L >= 5:                                                   # first floor: overflow racks & break room
            more = max(9, BRACKS[L] - racks)
            fit(d, 6, [("r", x, 14, 3) for x in range(22, 22 + (more + 2) // 3)] + [
                ("s", 25, 9, sl("birch", "top")), ("c", 24, 9, "west", False), ("c", 26, 9, "east", False),
                ("c", 25, 8, "north", False), ("c", 25, 10, "south", False), ("rug", 23, 7, 27, 11, "gray_carpet"),
                ("s", 21, 4, pot(3)), ("G", 25, 9, "sea_lantern")], "birch")
            racks += more
            neo_roof(d, hb, [(22, 31, 6, SOLAR), (22, 31, 9, SOLAR), (22, 31, 12, SOLAR)])
        else:
            neo_roof(d, hb, [(22, 24, 5, "iron_block", tr("iron", "north", "bottom"))] + [(22, 31, 9, SOLAR), (22, 31, 12, SOLAR)])
    # ---- prefab workshop (L4+), canteen above at L5
    if L >= 4:
        cs = 2 if L >= 5 else 1
        c = build(d, 3, 16, 17, 25, cs, roof="flat", core=(4, 18) if cs > 1 else None)
        c.door(10, 16, "north", double=True)
        rest = max(0, BRACKS[L] - racks) if L < 5 else 0
        fit(d, y0, [("i", 8, 24, "domum_ornamentum:architectscutter", "north"),
                    ("s", 7, 21, lg("stripped_birch_log", "x")), ("s", 8, 21, "crafting_table"),
                    ("s", 9, 21, sl("smooth_quartz", "top")), ("s", 10, 21, "stonecutter[facing=north]"),
                    ("s", 11, 21, sl("smooth_quartz", "top")), ("s", 12, 21, lg("stripped_birch_log", "x")),
                    ("s", 15, 24, "white_concrete"), ("o", 15, 24, "white_concrete"), ("s", 16, 24, "glass"),
                    ("s", 16, 20, "chest[facing=west,type=single,waterlogged=false]"), ("s", 12, 24, pot(3)),
                    ("G", 9, 19, FL), ("G", 9, 23, FL), ("G", 14, 21, FL)] +
            [("r", x, 24, 3) for x in range(4 if cs == 1 else 6, (4 if cs == 1 else 6) + (rest + 2) // 3)], "birch")
        racks += rest
        if cs > 1:                                                   # canteen over the workshop
            fit(d, 6, [("s", 8, 24, "smoker[facing=north,lit=false]"), ("s", 9, 24, sl("smooth_quartz", "top")),
                       ("s", 10, 24, "water_cauldron[level=3]"), ("s", 11, 24, "furnace[facing=north,lit=false]"),
                       ("s", 12, 24, sl("smooth_quartz", "top"))] +
                [("s", x, 21, sl("birch", "top")) for x in range(8, 13)] +
                [("c", x, 20, "north", False) for x in range(8, 13)] + [("c", x, 22, "south", False) for x in range(8, 13)] +
                [("s", 16, 17, pot(3)), ("s", 16, 24, pot(0)), ("G", 10, 19, "sea_lantern"), ("G", 10, 23, "sea_lantern")],
                "birch")
            neo_roof(d, c, [(5, 15, 18, MOSS), (5, 15, 19, 'azalea'), (5, 15, 21, MOSS), (5, 15, 22, 'azalea')])
        else:
            neo_roof(d, c, [(5, 15, 18, SOLAR), (5, 15, 21, SOLAR)])
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
        path(d, 20, 17, 33, 28, "gray_concrete")
        path(d, 24, 17, 26, 28, "yellow_concrete")
        for x, z, b, h in ((22, 19, "stone_bricks", 2), (23, 19, "stone_bricks", 1), (22, 20, "bricks", 2),
                           (29, 19, "white_concrete", 2), (30, 19, "white_concrete", 1), (29, 20, "glass", 1)):
            for k in range(h):
                d.set(x, y0 + k, z, b)
        log_pile(d, 20, 25, 23, 26, y0, 2, "birch_log", "x")
        for x in (21, 33):
            lamp_post(d, x, 27, y0, P)
    if L >= 5:                                                       # site gatehouse kiosk at the yard entrance
        k = build(d, 28, 19, 33, 25, 1, roof="flat")
        k.door(30, 19, "north")
        fit(d, y0, [("s", 31, 23, sl("smooth_quartz", "top")), ("c", 31, 22, "north", False),
                    ("o", 31, 23, "white_candle[candles=1,lit=false,waterlogged=false]"), ("s", 29, 24, pot(3)),
                    ("s", 32, 24, "chest[facing=north,type=single,waterlogged=false]"), ("G", 30, 22, "sea_lantern")], "birch")
        neo_roof(d, k, [(30, 31, 21, MOSS), (30, 31, 23, 'azalea')])
        for z in (17, 20, 23, 26):
            lamp_post(d, 34, z, y0, P)
        for x in (20, 23):
            d.set(x, y0, 28, "moss_block")
            tree(d, x, 28, y0 + 1, "birch", 3, 1)
    # top up seats with a bench by the door
    if seats < BSEATS[L]:
        bench(d, 12, 1, y0, "north", BSEATS[L] - seats, "birch")
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
    # workshop: bench run on the back wall, racks by the door and in the corner, plan desk at the front window,
    # fireside rug by the inglenook
    run = [("i", 5, 12, "crafting_table"), ("i", 6, 12, "cartography_table"),
           ("i", 7, 12, "barrel", "north"), ("i", 8, 12, "barrel", "north")]
    if L >= 2:
        run += [("i", 9, 12, "smithing_table"), ("i", 10, 12, "anvil", "east"), ("i", 11, 12, "grindstone", "north"),
                ("i", 12, 12, "stonecutter", "north")] + ([("i", 13, 12, "hopper")] if L <= 3 else [])
    if L >= 5:
        run += [("i", 13, 12, "ender_chest", "north")]
    racks = BRACKS[L] if L <= 2 else 9
    rk = [("r", 4, 5, 3), ("r", 4, 6, 3), ("r", 4, 11, 3)] + ([("r", 15, 12, 3)] if racks > 9 else [])
    seats = fit(d, y0, run + rk + [
        ("s", 11, 5, sl("dark_oak", "top")), ("s", 12, 5, sl("dark_oak", "top")), ("c", 11, 6, "south"),
        ("c", 12, 6, "south"), ("o", 11, 5, "candle[candles=2,lit=false,waterlogged=false]"),
        ("rug", 6, 8, 7, 10, "red_carpet"), ("st", 7, 8, "north"), ("st", 7, 10, "south"),
        ("s", 16, 12 if racks <= 9 else 11, pot(2)) if L == 1 else ("s", 14, 12, pot(2)),
        ("L", 9, 8), ("L", 13, 10)], "dark_oak")
    if sto >= 2:                                                     # drafting room & library upstairs
        seats += fit(d, 6, [("k", x, 12, 2) for x in range(5, 11)] + [
            ("i", 11, 12, "lectern", "north"), ("i", 12, 12, "cartography_table"), ("i", 13, 12, "crafting_table"),
            ("s", 7, 6, sl("dark_oak", "top")), ("s", 8, 6, sl("dark_oak", "top")), ("c", 7, 7, "south"),
            ("c", 8, 7, "south"), ("o", 8, 6, "candle[candles=3,lit=false,waterlogged=false]"),
            ("rug", 6, 9, 10, 10, "red_carpet"), ("s", 13, 4, pot(0)), ("L", 9, 9)] +
            ([("i", 5, 4, "jukebox")] if L >= 4 else []), "dark_oak")
    if sto >= 3:                                                     # top floor: apprentices' dormitory
        fit(d, 10, [("bed", x, 12, "south") for x in (6, 9, 12)] +
            [("s", x, 12, sl("oak", "top")) for x in (7, 10)] + [("o", 7, 12, "candle[candles=1,lit=false,waterlogged=false]"),
             ("s", 5, 4, "chest[facing=south,type=single,waterlogged=false]"),
             ("s", 6, 4, "chest[facing=south,type=single,waterlogged=false]"),
             ("s", 9, 7, "oak_fence"), ("o", 9, 7, "oak_pressure_plate[powered=false]"),
             ("c", 8, 7, "west", False), ("c", 10, 7, "east", False), ("L", 9, 8)], "oak")
    # window boxes on the street front
    if sto >= 2:
        for x in (5, 11, 14):
            flower_box(d, x, 6, 3, "north", "dark_oak", ("red_tulip", "oxeye_daisy", "cornflower")[x % 3])
    else:
        for x in (5, 14):
            flower_box(d, x, 2, 3, "north", "dark_oak", "red_tulip")
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
        cols = {3: 5, 4: 9, 5: 12}[L]                               # shelving bays across the barn
        cells = [(x, 6) for x in range(21, 27)] + [(x, 7) for x in range(21, 27)]
        fit(d, bb.stand(0), [("r", x, z, 3) for x, z in cells[:cols]] + [
            ("s", 21, 18, "stone_bricks"), ("o", 21, 18, "stone_bricks"), ("s", 22, 18, "cobblestone"),
            ("s", 28, 4, "chest[facing=west,type=single,waterlogged=false]"), ("L", 24, 9), ("L", 24, 13)])
        log_pile(d, 21, 14, 25, 16, bb.stand(0), 2, "oak_log", "x")
        racks += cols * 3
        if bs > 1:                                                   # timber loft
            fit(d, 6, [("s", 21, 5, "oak_planks"), ("o", 21, 5, sl("oak")), ("s", 21, 6, "oak_planks"),
                       ("s", 22, 18, "white_wool"), ("s", 21, 18, "brown_wool"), ("o", 21, 18, "brown_carpet"),
                       ("L", 24, 9)])
            log_pile(d, 21, 9, 24, 10, 6, 1, "stripped_oak_log", "x")
        d.sign(23, 6, 2, "north", ["Timber", "& Stone Store"], "dark_oak")
    # ---- mason's lodge (L4+), upper floor at L5
    if L >= 4:
        cs = 2
        c = build(d, 3, 17, 15, 25, cs, roof="gable", axis="x", core=(4, 19) if cs > 1 else None,
                  chimney=(14, 21, "west"))
        c.door(9, 17, "north", double=True)
        # mason's banker benches, cutter by the back wall; master's quarters with desk and bookcase above
        seats += fit(d, y0, [("i", 8, 24, "domum_ornamentum:architectscutter", "north"),
                             ("s", 8, 21, "stone_bricks"), ("s", 9, 21, "chiseled_stone_bricks"),
                             ("s", 10, 21, sl("stone_brick", "top")), ("c", 8, 20, "north"), ("c", 10, 20, "north"),
                             ("s", 12, 24, "stone_bricks"), ("o", 12, 24, sl("stone_brick")), ("s", 13, 24, "cobblestone"),
                             ("s", 7, 18, "water_cauldron[level=3]"), ("L", 9, 19), ("L", 11, 23)], "dark_oak")
        seats += fit(d, 6, [("bed", 12, 24, "south"), ("s", 11, 24, sl("dark_oak", "top")),
                            ("o", 11, 24, "candle[candles=1,lit=false,waterlogged=false]"),
                            ("s", 8, 24, sl("dark_oak", "top")), ("c", 8, 23, "north"),
                            ("s", 9, 24, sl("dark_oak", "top")), ("c", 9, 23, "north"),
                            ("k", 6, 24, 2), ("k", 7, 24, 2), ("rug", 8, 20, 11, 21, "red_carpet"),
                            ("s", 13, 18, pot(2)), ("L", 9, 21)], "dark_oak")
    if L >= 5:                                                       # guild hall closing the yard
        g = build(d, 19, 21, 31, 28, 3, roof="gable", axis="x", core=(29, 23), chimney=(20, 25, "east"))
        g.door(24, 21, "north", double=True)
        # feast hall: long table with benches before the hearth; library above; model loft in the roof
        fit(d, y0, [("s", x, 25, sl("dark_oak", "top")) for x in range(22, 28)] +
            [("c", x, 24, "north", False) for x in range(22, 28)] + [("c", x, 26, "south", False) for x in range(22, 28)] +
            [("s", 27, 22, "barrel[facing=north,open=false]"), ("s", 26, 22, "barrel[facing=north,open=false]"),
             ("s", 22, 22, pot(2)), ("L", 23, 23), ("L", 26, 23)], "dark_oak")
        fit(d, 6, [("k", x, 27, 2) for x in range(21, 27)] + [
            ("s", 24, 24, "dark_oak_fence"), ("o", 24, 24, "dark_oak_pressure_plate[powered=false]"),
            ("c", 23, 24, "west", False), ("c", 25, 24, "east", False), ("rug", 22, 23, 26, 25, "red_carpet"),
            ("s", 21, 22, pot(0)), ("L", 25, 24)], "dark_oak")
        fit(d, 10, [("s", 22, 24, "oak_planks"), ("o", 22, 24, sl("oak")), ("s", 24, 24, "bricks"),
                    ("o", 24, 24, sl("brick")), ("s", 26, 24, "stone_bricks"), ("s", 21, 27, "white_wool"),
                    ("s", 22, 27, "brown_wool"), ("s", 27, 27, "chest[facing=north,type=single,waterlogged=false]"),
                    ("L", 25, 25)])
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
        for x in (4, 12):
            tree(d, x, 27, y0, "oak", 4, 1)
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
    # barn floor: saw horse in the nave, bench & cabinets on the east wall, rack bay, plan desk by the doors
    sawhorse(d, 9, 9, y0, "spruce", "x")
    run = [("i", 16, 7, "crafting_table"), ("i", 16, 8, "cartography_table"), ("i", 16, 9, "barrel", "west"),
           ("i", 16, 10, "barrel", "west")]
    if L >= 2:
        run += [("i", 16, 11, "smithing_table"), ("i", 16, 12, "anvil", "north"), ("i", 16, 13, "grindstone", "west"),
                ("i", 16, 14, "stonecutter", "west")] + ([("i", 14, 15, "hopper")] if L <= 3 else [])
    racks = min(BRACKS[L], 12)
    rk = [("r", 6, z, 3) for z in (6, 7, 8)] if L == 1 else [("r", x, 15, 3) for x in (9, 10, 11, 12)]
    seats = fit(d, y0, run + rk + [
        ("s", 13, 5, sl("spruce", "top")), ("s", 14, 5, sl("spruce", "top")), ("c", 13, 6, "south"),
        ("c", 14, 6, "south"), ("o", 14, 5, "candle[candles=2,lit=false,waterlogged=false]"),
        ("s", 9, 11 if L == 1 else 13, lg("spruce_log", "x")), ("s", 10, 11 if L == 1 else 13, lg("spruce_log", "x")),
        ("L", 11, 6), ("L", 11, 10 if L == 1 else 14)], "spruce")
    shutter_pair(d, 7, 3, 4, "north", "spruce")
    shutter_pair(d, 13, 3, 4, "north", "spruce")
    if sto >= 2:                                                     # plan loft with the library
        seats += fit(d, 6, [("k", 16, z, 2) for z in range(5, 11)] + [
            ("i", 9, 15, "lectern", "north"), ("i", 10, 15, "cartography_table"), ("i", 11, 15, "crafting_table"),
            ("s", 13, 13, sl("spruce", "top")), ("s", 14, 13, sl("spruce", "top")), ("c", 13, 12, "north"),
            ("c", 14, 12, "north"), ("o", 13, 13, "candle[candles=2,lit=false,waterlogged=false]"),
            ("rug", 10, 6, 13, 9, "green_carpet"), ("s", 6, 5, pot(0)), ("L", 11, 10)], "spruce")
    if sto >= 3:                                                     # hay & seasoning loft
        fit(d, 10, [("s", 9, 14, "hay_block[axis=y]"), ("s", 10, 14, "hay_block[axis=y]"),
                    ("o", 9, 14, "hay_block[axis=y]"), ("s", 12, 14, "white_wool"), ("s", 13, 14, "brown_wool"),
                    ("L", 11, 10)])
        log_pile(d, 14, 6, 15, 9, 10, 2, "stripped_spruce_log", "z")
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
        # cabin parlour: settle facing the stone fireplace, armchair, the drawing cabinet on the back wall
        seats += fit(d, y0, [("c", 9, z, "east") for z in (25, 26, 27)] + [
            ("c", 8, 28, "south"), ("s", 8, 26, sl("spruce", "top")), ("rug", 7, 25, 7, 27, "brown_carpet"),
            ("i", 8, 30, "domum_ornamentum:architectscutter", "north"), ("i", 10, 30, "jukebox")] +
            ([("i", 11, 30, "ender_chest", "north")] if L >= 5 else []) +
            [("s", 7, 22, pot(0)), ("L", 9, 23), ("L", 10, 28)], "spruce")
        fit(d, 6, [("bed", 8, 30, "south"), ("bed", 10, 30, "south"), ("s", 9, 30, sl("spruce", "top")),
                   ("o", 9, 30, "candle[candles=1,lit=false,waterlogged=false]"),
                   ("s", 7, 22, "chest[facing=south,type=single,waterlogged=false]"),
                   ("s", 8, 22, "chest[facing=south,type=single,waterlogged=false]"),
                   ("rug", 8, 26, 10, 28, "green_carpet"), ("L", 11, 26)], "spruce")
        bench(d, 5, 19, y0, "south", 2, "spruce", sit=False)
        for z in (20, 26, 31):
            lamp_post(d, 18, z, y0, P)
    # ---- smithy lean-to and log yard (L5)
    if L >= 5:
        sm = build(d, 20, 21, 30, 29, 2, roof="gable", axis="z", core=(28, 23), chimney=(21, 26, "east"))
        sm.door(25, 21, "north", double=True)
        rest = max(0, BRACKS[L] - racks)
        fit(d, y0, [("s", 23, 25, "anvil[facing=north]"), ("s", 23, 27, "grindstone[face=floor,facing=north]"),
                    ("s", 22, 23, "water_cauldron[level=3]"), ("s", 25, 28, lg("spruce_log", "x")),
                    ("s", 26, 28, "chest[facing=north,type=single,waterlogged=false]"), ("L", 25, 25)] +
            [("r", x, 28, 3) for x in range(22, 22 + (rest + 2) // 3)], "spruce")
        racks += rest
        fit(d, 6, [("s", 24, 25, sl("spruce", "top")), ("s", 25, 25, sl("spruce", "top")),
                   ("c", 24, 24, "north", False), ("c", 25, 24, "north", False),
                   ("c", 24, 26, "south", False), ("c", 25, 26, "south", False),
                   ("s", 22, 28, "barrel[facing=north,open=false]"), ("s", 23, 28, "barrel[facing=north,open=false]"),
                   ("L", 25, 23)], "spruce")
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
    if L >= 4:
        spot_trees(d, [(32, 18), (32, 12)], "spruce", 5)
        for z in (20, 24):
            lamp_post(d, 33, z, y0, P)
    if L >= 5:
        spot_trees(d, [(32, 6), (19, 33)], "spruce", 5)
        lamp_post(d, 33, 28, y0, P)
    if seats < BSEATS[L]:
        bench(d, 13, 2, y0, "north", BSEATS[L] - seats, "spruce")
    tree(d, 32, 32, y0, "spruce", 5, 2)
    tree(d, 1, 32, y0, "spruce", 5, 2) if L < 5 else None
    return d


@design("builder")
def builder(pack, rel, L):
    return demote({"Neoterra": builder_neo, "Hearthwood": builder_hw, "Cascadia": builder_cas}[pack](rel, L), L)


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
    n = SAWS[L]
    saw_line(d, [(x, 9) for x in range(6, 6 + n + 2)], y0, n, "stripped_mangrove_log")
    # saw hall: foreman's bench by the hut, timber racks with stacked boards on the back wall, ceiling lights
    FL = "pearlescent_froglight[axis=y]"
    rx = [5, 7, 9, 11, 13][:L]
    fit(d, y0, [("i", 4, 7, "crafting_table")] + [("r", x, 12, 1) for x in rx] +
        [("s", x, 12, "birch_planks") for x in (6, 8, 10, 12, 14) if x < x2 - 1] +
        [("o", x, 12, sl("mangrove")) for x in (6, 10) if x < x2 - 1] +
        [("s", 4, 11, "chest[facing=east,type=single,waterlogged=false]"), ("s", 4, 12, pot(3)),
         ("G", 7, 7, FL, 6), ("G", 11, 7, FL, 6), ("G", 7, 11, FL, 6), ("G", 11, 11, FL, 6)] +
        ([("G", 16, 7, FL, 6), ("G", 16, 11, FL, 6), ("s", 18, 12, lg("birch_log", "x")),
          ("s", 19, 12, lg("birch_log", "x")), ("o", 18, 12, lg("birch_log", "x"))] if L >= 2 else []), "mangrove")
    for x in range(6, 8 + n):
        d.set(x, 1, 8, "orange_concrete")
        d.set(x, 1, 10, "orange_concrete")
    # forecourt
    for x in (1, x2 + 2):
        d.set(x, y0, 3, "moss_block")
        tree(d, x, 3, y0 + 1, "birch", 3, 1)
    lamp_post(d, 13, 2, y0, P)
    if L >= 2:
        for x in (1, 22):
            lamp_post(d, x, 6, y0, P)
        lamp_post(d, 22, 12, y0, P)
    if L >= 4:
        spot_trees(d, [(34, 14), (34, 20), (34, 26)], "birch", 3)
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
        # ground: mill office (desks along the west wall, plans on the lectern); first floor: staff canteen
        fit(d, y0, [("i", 25, 11, "lectern", "north"), ("i", 26, 11, "cartography_table"),
                    ("s", 25, 7, sl("smooth_quartz", "top")), ("c", 26, 7, "east", False),
                    ("s", 25, 9, sl("smooth_quartz", "top")), ("c", 26, 9, "east", False),
                    ("o", 25, 7, "white_candle[candles=1,lit=false,waterlogged=false]"),
                    ("rug", 27, 6, 28, 9, "orange_carpet"), ("s", 28, 11, pot(3)), ("G", 27, 8, "sea_lantern")],
            "mangrove")
        fit(d, 6, [("s", 25, 11, "smoker[facing=north,lit=false]"), ("s", 26, 11, sl("smooth_quartz", "top")),
                   ("s", 27, 11, "water_cauldron[level=3]"), ("s", 28, 11, "furnace[facing=north,lit=false]"),
                   ("s", 26, 8, sl("mangrove", "top")), ("s", 27, 8, sl("mangrove", "top")),
                   ("c", 26, 7, "north", False), ("c", 27, 7, "north", False),
                   ("c", 26, 9, "south", False), ("c", 27, 9, "south", False), ("s", 25, 5, pot(0)),
                   ("G", 27, 6, "sea_lantern")], "mangrove")
        if so >= 3:
            fit(d, 10, [("k", 25, z, 2) for z in (6, 7, 8)] + [
                ("s", 27, 9, sl("mangrove", "top")), ("c", 27, 8, "north", False), ("c", 27, 10, "south", False),
                ("s", 28, 6, pot(3)), ("rug", 26, 9, 26, 10, "orange_carpet"), ("G", 27, 7, "sea_lantern")], "mangrove")
            neo_roof(d, b, [(26, 30, 6, MOSS), (26, 30, 8, 'azalea'), (26, 30, 10, MOSS)])
        else:
            neo_roof(d, b, [(26, 30, 6, SOLAR), (26, 30, 9, SOLAR)])
        bench(d, 28, 2, y0, "north", 2, "mangrove", sit=False)
    # ---- drying kiln (L4+)
    if L >= 4:
        k = build(d, 21, 16, 32, 25, 2 if L == 4 else 3, roof="flat", core=(22, 18))
        k.door(27, 16, "north", double=True)
        # kiln floors: boards stacked on stickers in two rows, the architect's cutter by the door
        fit(d, y0, [("i", 30, 24, "domum_ornamentum:architectscutter", "north")] +
            [("s", x, 21, "birch_planks") for x in (26, 27, 28, 29)] +
            [("o", x, 21, sl("birch")) for x in (26, 27, 28, 29)] +
            [("s", x, 23, lg("stripped_birch_log", "x")) for x in (26, 27, 28)] +
            [("G", 27, 19, "pearlescent_froglight[axis=y]"), ("G", 29, 22, "pearlescent_froglight[axis=y]")])
        for s_ in range(1, k.storeys):
            yy = k.stand(s_)
            fit(d, yy, [("s", x, z, "birch_planks") for x in (26, 27, 28, 29) for z in (20, 23)] +
                [("o", x, z, "stripped_birch_wood[axis=x]") for x in (26, 28) for z in (20, 23)] +
                [("G", 27, 22, "pearlescent_froglight[axis=y]")])
        for x in (23, 26, 29):                                        # roof vents
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
    n = SAWS[L]
    saw_line(d, [(8, z) for z in range(5, 5 + n + 2)], y0, n, "stripped_oak_log", "z")
    d.set(13, y0, 9, "grindstone[face=floor,facing=east]")       # gear train
    d.fill(13, y0 + 1, 9, 13, 3, 9, lg("dark_oak_log", "y"))
    d.set(13, 4, 9, lg("dark_oak_log", "x"))
    racks = min(L, 3)
    # mill floor: sawyer's bench by the door, board racks on the west wall, a log ready at the in-feed
    zz = z2 - 1
    fit(d, y0, [("i", 5, 7, "crafting_table")] + [("r", 5, z, 1) for z in (9, 10, 11)[:racks]] + [
        ("s", 6, zz, "chest[facing=north,type=single,waterlogged=false]"), ("s", 10, zz, "oak_planks"),
        ("o", 10, zz, sl("oak")), ("s", 11 if sto == 1 else 13, 5 if sto == 1 else 14, pot(2)),
        ("L", 9, 6), ("L", 9, 10)], "oak")
    if sto >= 2:                                                     # sack floor over the saws
        fit(d, 6, [("r", 5, z, 1) for z in (6, 7)[:L - racks]] + [
            ("s", 6, zz, "white_wool"), ("s", 7, zz, "brown_wool"), ("o", 6, zz, "white_wool"),
            ("s", 9, zz, "hay_block[axis=y]"), ("s", 5, zz, "chest[facing=east,type=single,waterlogged=false]"),
            ("L", 8, 10)])
        log_pile(d, 6, 9, 9, 10, 6, 1, "stripped_oak_log", "x")
        racks = L
    if sto >= 3:                                                     # grain & sack loft
        fit(d, 10, [("s", 6, zz, "hay_block[axis=y]"), ("o", 6, zz, "hay_block[axis=y]"), ("s", 7, zz, "white_wool"),
                    ("s", 5, 9, "brown_wool"), ("s", 5, 10, "white_wool"), ("L", 8, 10)])
    if L >= 4:
        spot_trees(d, [(1, 18), (1, 24), (14, 27)], "oak", 4)
    if L >= 5:
        for z in (6, 12):
            lamp_post(d, 1, z, y0, P)
        spot_trees(d, [(31, 27), (31, 2)], "oak", 4)
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
        # sawyer's cottage: office & settle by the fire below, bedroom above, parlour in the attic (L5)
        fit(d, y0, [("i", 23, 10, "lectern", "north"), ("i", 24, 10, "cartography_table"),
                    ("s", 26, 10, sl("oak", "top")), ("c", 26, 9, "north", False),
                    ("o", 26, 10, "candle[candles=2,lit=false,waterlogged=false]"),
                    ("c", 23, 7, "east", False), ("c", 23, 9, "east", False), ("rug", 22, 7, 22, 9, "red_carpet"),
                    ("s", 26, 5, pot(2)), ("L", 25, 7)], "oak")
        fit(d, 6, [("bed", 23, 10, "south"), ("bed", 25, 10, "south"), ("s", 24, 10, sl("oak", "top")),
                   ("o", 24, 10, "candle[candles=1,lit=false,waterlogged=false]"),
                   ("s", 22, 5, "chest[facing=south,type=single,waterlogged=false]"),
                   ("s", 23, 5, "chest[facing=south,type=single,waterlogged=false]"),
                   ("rug", 23, 7, 25, 8, "orange_carpet"), ("L", 26, 7)], "oak")
        if L >= 5:
            fit(d, 10, [("c", x, 8, "south", False) for x in (24, 25, 26)] + [
                ("s", 25, 6, sl("oak", "top")), ("s", 22, 5, pot(0)), ("s", 22, 10, pot(4)), ("L", 26, 7)], "oak")
        for x in range(20, 31):
            if x not in (24,):
                d.set(x, y0, 2, "oak_fence")
        flower_bed(d, 21, 3, 22, 3, y0, seed=2) if False else None
        tree(d, 32, 3, y0, "oak", 4, 1)
    # ---- plank drying barn (L4+), wheelwright & cart shed (L5)
    if L >= 4:
        c = build(d, 20, 15, 30, 25, 2, roof="gable", axis="z", core=(28, 17))
        c.opening(24, 15, 26, 15, 3, lg("stripped_oak_log", "x"))
        for z in (16, 20, 24, 28):
            lamp_post(d, 32, z, y0, P)
        # drying barn: plank stacks on bearers in two rows each floor
        fit(d, y0, [("i", 21, 24, "domum_ornamentum:architectscutter", "east")] +
            [("s", x, 20, "oak_planks") for x in (22, 23, 24, 25)] + [("o", x, 20, "oak_planks") for x in (22, 24)] +
            [("s", x, 23, lg("stripped_oak_log", "x")) for x in (23, 24, 25)] + [("L", 25, 18), ("L", 25, 22)])
        fit(d, 6, [("s", x, 23, "oak_planks") for x in (22, 23, 24, 25)] + [("o", x, 23, sl("oak")) for x in (22, 23)] +
            [("s", x, 19, "spruce_planks") for x in (23, 24, 25)] + [("L", 25, 21)])
    if L >= 5:
        e = build(d, 3, 19, 13, 27, 2, roof="gable", axis="x", core=(4, 21))
        e.opening(7, 19, 9, 19, 3, lg("stripped_oak_log", "x"))
        wagon(d, 8, 24, y0, "oak", "oak_planks")
        fit(d, y0, [("s", 12, 26, "hay_block[axis=y]"), ("s", 12, 25, "white_wool"),
                    ("s", 7, 21, "chest[facing=south,type=single,waterlogged=false]"), ("L", 9, 21)])
        # wheelwright's loft: anvil, grindstone, a wheel in the making
        fit(d, 6, [("s", 9, 26, "anvil[facing=east]"), ("s", 10, 26, "grindstone[face=floor,facing=north]"),
                   ("s", 11, 26, "oak_planks"), ("o", 11, 26, sl("oak")), ("s", 9, 23, lg("stripped_oak_log", "x")),
                   ("s", 10, 23, lg("stripped_oak_log", "x")), ("s", 12, 21, pot(2)), ("L", 9, 24)], "oak")
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
        # mill office: pay window and ledger desk below, the boss's desk and map case above
        fit(d, y0, [("i", 26, 8, "lectern", "north"), ("i", 26, 6, "cartography_table"),
                    ("s", 30, 8, "chest[facing=west,type=single,waterlogged=false]"), ("s", 30, 6, pot(0)),
                    ("s", 30, 4, "oak_fence"), ("o", 30, 4, "spruce_pressure_plate[powered=false]"),
                    ("L", 26, 5)], "spruce")
        fit(d, 6, [("s", 26, 8, sl("spruce", "top")), ("c", 26, 7, "north", False),
                   ("o", 26, 8, "candle[candles=2,lit=false,waterlogged=false]"), ("k", 30, 8, 2), ("k", 30, 7, 1),
                   ("s", 30, 5, pot(3)), ("L", 26, 5)], "spruce")
    # ---- planing mill (L4+)
    if L >= 4:
        c = build(d, 4, 21, 16, 29, 2, roof="gable", axis="x", core=(14, 23))
        c.opening(8, 21, 10, 21, 3, lg("spruce_log", "x"))
        # planing mill: planer bench across the floor, cutter by the wall; board loft above
        fit(d, y0, [("i", 6, 28, "domum_ornamentum:architectscutter", "north"),
                    ("s", 8, 25, "spruce_planks"), ("s", 9, 25, lg("stripped_spruce_log", "x")),
                    ("s", 10, 25, "grindstone[face=floor,facing=north]"), ("s", 11, 25, lg("stripped_spruce_log", "x")),
                    ("s", 12, 25, "spruce_planks"), ("s", 12, 28, "spruce_planks"), ("o", 12, 28, sl("spruce")),
                    ("s", 11, 28, "dark_oak_planks"), ("L", 9, 23), ("L", 10, 27)], "spruce")
        fit(d, 6, [("s", x, 27, "spruce_planks") for x in (6, 7, 8, 9)] + [("o", x, 27, "dark_oak_planks") for x in (6, 7)] +
            [("s", x, 24, "stripped_spruce_wood[axis=x]") for x in (7, 8, 9)] + [("L", 10, 25)])
    # ---- bunkhouse and log flume (L5)
    if L >= 5:
        e = build(d, 19, 22, 25, 31, 2, roof="gable", axis="z", core=(20, 24), chimney=(24, 28, "west"))
        e.door(22, 22, "north")
        # bunkhouse: cook stove and mess table below, bunks above
        fit(d, y0, [("s", 24, 24, "smoker[facing=west,lit=false]"), ("s", 24, 25, "water_cauldron[level=3]"),
                    ("s", 23, 26, sl("spruce", "top")), ("s", 23, 27, sl("spruce", "top")),
                    ("c", 22, 26, "west", False), ("c", 22, 27, "west", False), ("s", 23, 30, "barrel[facing=north,open=false]"),
                    ("L", 23, 28)], "spruce")
        fit(d, 6, [("bed", 23, 30, "south"), ("bed", 24, 24, "east"), ("s", 24, 30, sl("spruce", "top")),
                   ("o", 24, 30, "candle[candles=1,lit=false,waterlogged=false]"),
                   ("s", 22, 30, "chest[facing=north,type=single,waterlogged=false]"), ("L", 23, 27)], "spruce")
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
    return demote({"Neoterra": saw_neo, "Hearthwood": saw_hw, "Cascadia": saw_cas}[pack](rel, L), L)


# =============================================================================================== LUMBERJACK
"""
Lumberjack
  Neoterra   "Urban forestry station" (birch cladding, white fins, lime bands, green roofs): forestry pavilion
             (rangers' office upstairs from L2), sapling nursery planters, covered log store; glass nursery
             greenhouse with a seating corner (L3); two-storey equipment depot (L4); ranger watch tower (L5).
  Hearthwood "Woodcutter's cottage" (white-washed walls on a rubble plinth, spruce shingle roofs): cottage with a
             big chimney (bedroom upstairs from L2), log store lean-to, chopping block and saw horse; log barn
             (L3); charcoal-burner's hut with a smouldering clamp and fenced garden (L4); timber storehouse (L5).
  Cascadia   "Forester's lodge" (dark spruce logs, red-cedar roofs, forest-green trim): steep log lodge with a
             front deck (loft from L2), woodshed and rockers (L3), fire lookout tower (L4), crew bunkhouse (L5).
"""
JACK_RACKS = {1: 2, 2: 3, 3: 4, 4: 5, 5: 6}


def jack_neo(rel, L):
    d = Design("Neoterra", rel, (30, 26, 30), paving="smooth_stone")
    P, y0 = "Neoterra", 2
    sto = 1 if L == 1 else 2
    a = build(d, 3, 4, 13, 11, sto, roof="flat", core=(11, 6) if sto > 1 else None, street_glass=True)
    a.door(6, 4, "north", double=True)
    d.hut(4, y0, 5)
    d.sign(9, 5, 3, "north", ["FORESTRY", "STATION"], "birch", glow=True, color="lime")
    # ranger room: tool bench and gear racks by the back wall, map table; rangers' office upstairs
    racks = min(JACK_RACKS[L], 3)
    fit(d, y0, [("i", 5, 10, "crafting_table", "north"), ("s", 6, 10, "grindstone[face=floor,facing=north]"),
                ("r", 4, 8, 1), ("r", 4, 9, 1)] + ([("r", 7, 10, 1)] if racks > 2 else []) + [
        ("s", 8, 7, sl("birch", "top")), ("o", 8, 7, "potted_oak_sapling"), ("c", 8, 8, "south", False),
        ("s", 9, 10, "chest[facing=north,type=single,waterlogged=false]"), ("s", 12, 10 if L == 1 else 5, pot(3)),
        ("G", 6, 7, "pearlescent_froglight[axis=y]"), ("G", 9, 8, "pearlescent_froglight[axis=y]")], "birch")
    if sto >= 2:
        n1 = JACK_RACKS[L] - racks
        fit(d, 6, [("r", 4, z, 1) for z in (6, 7, 8)[:n1]] + [
            ("s", 6, 10, sl("birch", "top")), ("c", 6, 9, "north", False), ("s", 8, 10, sl("birch", "top")),
            ("c", 8, 9, "north", False), ("o", 6, 10, "white_candle[candles=1,lit=false,waterlogged=false]"),
            ("k", 5, 10, 2), ("s", 9, 5, pot(0)), ("G", 7, 8, "sea_lantern")], "birch")
        racks = JACK_RACKS[L]
        neo_roof(d, a, [(5, 11, 6, MOSS), (5, 11, 7, 'azalea'), (5, 11, 8, MOSS), (5, 11, 9, 'azalea')])
    else:
        neo_roof(d, a, [(5, 11, 6, MOSS), (5, 11, 8, 'azalea')])
    # covered log store (west), nursery planters (east)
    for z in (4, 11):
        d.fill(1, y0, z, 1, 4, z, "light_gray_concrete")
    d.fill(0, 5, 4, 2, 5, 11, sl("smooth_quartz"))
    log_pile(d, 1, 5, 2, 10, y0, 3, "birch_log", "z")
    for x in range(15, 21):
        for z in (4, 5, 7, 8):
            d.set(x, 1, z, "moss_block")
            d.set(x, y0, z, "birch_sapling[stage=0]" if (x + z) % 2 else "oak_sapling[stage=0]")
    for x in range(14, 22):
        d.set(x, y0, 3, sl("smooth_quartz"))
    lamp_post(d, 14, 1, y0, P)
    seats = 0
    if L >= 2:
        sawhorse(d, 15, 12, y0, "birch")
        log_pile(d, 15, 14, 21, 15, y0, 2, "oak_log", "x")
    # ---- nursery greenhouse (L3+)
    if L >= 3:
        gx1, gz1, gx2, gz2 = 3, 15, 13, 22
        d.box(gx1, y0, gz1, gx2, 5, gz2, "glass", floor="smooth_stone")
        d.fill(gx1, 6, gz1, gx2, 6, gz2, "glass")
        for x, z in ring(gx1, gz1, gx2, gz2):
            if (x - gx1) % 5 == 0 and z in (gz1, gz2) or x in (gx1, gx2) and (z - gz1) % 7 == 0:
                d.fill(x, y0, z, x, 6, z, "white_concrete")
        d.door(8, y0, gz1, "north", "birch")
        d.door(8, y0, 11, "south", "birch")
        for x in range(gx1 + 1, gx2):
            for z in (gz2 - 1, gz2 - 2):
                d.set(x, 1, z, "moss_block")
                d.set(x, y0, z, ["spruce_sapling[stage=0]", "birch_sapling[stage=0]", "fern", "azalea"][(x + z) % 4])
        d.chair(gx1 + 1, y0, gz1 + 2, "west", "birch")
        d.chair(gx1 + 1, y0, gz1 + 4, "west", "birch")
        d.table(gx1 + 1, y0, gz1 + 3, "birch", "slab")
        seats = 2
        for x in (5, 11):
            d.set(x, 5, 18, "end_rod[facing=down]")
        for z in (14, 18, 22):                                       # avenue of young birches
            d.set(0, y0, z, "moss_block")
            tree(d, 0, z, y0 + 1, "birch", 3, 1)
        for x in (15, 19):
            lamp_post(d, x, 24, y0, P) if L < 5 else None
        bench(d, 15, 10, y0, "south", 2, "birch", sit=False)
        for x in (24, 27):
            d.set(x, y0, 3, "moss_block")
            tree(d, x, 3, y0 + 1, "birch", 3, 1)
        if L >= 4:
            d.item(gx2 - 1, y0, gz1 + 2, "composter")
            d.item(gx2 - 1, y0, gz1 + 3, "barrel", "west")
    # ---- equipment depot (L4+)
    if L >= 4:
        c = build(d, 16, 12, 26, 20, 2, roof="flat", core=(24, 14))
        c.opening(19, 12, 21, 12, 3, "lime_concrete")
        # equipment depot: sharpening bench, log stock and gear chests; crew canteen above
        fit(d, y0, [("s", 18, 19, "anvil[facing=east]"), ("s", 19, 19, "grindstone[face=floor,facing=north]"),
                    ("s", 20, 19, sl("birch", "top")), ("s", 17, 14, "chest[facing=east,type=single,waterlogged=false]"),
                    ("s", 17, 15, "chest[facing=east,type=single,waterlogged=false]"),
                    ("G", 20, 15, "pearlescent_froglight[axis=y]"), ("G", 20, 18, "pearlescent_froglight[axis=y]")], "birch")
        log_pile(d, 18, 17, 21, 17, y0, 1, "birch_log", "x")
        fit(d, 6, [("s", 18, 19, "smoker[facing=north,lit=false]"), ("s", 19, 19, sl("smooth_quartz", "top")),
                   ("s", 20, 19, "water_cauldron[level=3]"), ("s", 21, 19, "furnace[facing=north,lit=false]"),
                   ("s", 19, 16, sl("birch", "top")), ("s", 20, 16, sl("birch", "top")),
                   ("c", 19, 15, "north", False), ("c", 20, 15, "north", False),
                   ("c", 19, 17, "south", False), ("c", 20, 17, "south", False), ("s", 17, 13, pot(3)),
                   ("G", 20, 14, "sea_lantern")], "birch")
        neo_roof(d, c, [(18, 22, 14, SOLAR), (18, 22, 17, SOLAR)])
        wagon(d, 22, 23, y0, "birch", lg("birch_log", "x")) if L == 4 else None
    # ---- ranger watch tower (L5)
    if L >= 5:
        t = build(d, 18, 21, 24, 28, 5, roof="flat", core=(19, 23))
        t.door(24, 25, "east")
        # ranger tower floors (east half beside the stair): desk, map room, bunk, archive, lookout lounge
        y_ = [t.stand(s) for s in range(5)]
        fit(d, y_[0], [("s", 23, 22, sl("birch", "top")), ("c", 22, 22, "west", False), ("s", 23, 27, pot(3)),
                       ("G", 22, 26, "sea_lantern")], "birch")
        fit(d, y_[1], [("s", 23, 23, sl("birch", "top")), ("o", 23, 23, "potted_spruce_sapling"),
                       ("c", 22, 23, "west", False), ("k", 23, 27, 2), ("G", 22, 26, "sea_lantern")], "birch")
        fit(d, y_[2], [("bed", 23, 27, "south", "lime"), ("s", 22, 22, "chest[facing=east,type=single,waterlogged=false]"),
                       ("s", 23, 22, pot(0)), ("G", 22, 24, "sea_lantern")], "birch")
        fit(d, y_[3], [("k", 23, z, 2) for z in (22, 23)] + [("s", 23, 27, sl("birch", "top")),
                                                             ("c", 22, 27, "west", False), ("G", 22, 25, "sea_lantern")], "birch")
        fit(d, y_[4], [("c", 23, 26, "east", False), ("c", 23, 27, "east", False), ("s", 23, 22, pot(3)),
                       ("G", 22, 24, "sea_lantern")], "birch")
        # glazed lookout on top
        for x, z in ring(17, 20, 25, 29):
            d.set(x, t.yr + 1, z, "glass_pane" if (x + z) % 2 else "white_concrete")
        d.set(21, t.yr + 3, 24, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        for x in (27, 28):
            for z in (22, 26):
                d.set(x, y0, z, "moss_block")
                tree(d, x, z, y0 + 1, "spruce", 4, 1)
    return d


def jack_hw(rel, L):
    d = Design("Hearthwood", rel, (32, 20, 30), paving="gravel")
    P, y0 = "Hearthwood", 2
    sto = 1 if L == 1 else 2
    a = build(d, 6, 4, 15, 10, sto, roof="gable", axis="x", core=(13, 5) if False else None,
              chimney=(14, 7, "west"))
    a.door(9, 4, "north")
    d.hut(7, y0, 5)
    # parlour-kitchen with the hearth: settle facing the fire, work table, tools on the wall
    racks = min(JACK_RACKS[L], 2)
    seats = fit(d, y0, [("i", 8, 9, "crafting_table", "north"), ("r", 10, 9, 1), ("r", 11, 9, 1)][:1 + racks] + [
        ("c", 12, 6, "west", L >= 3), ("c", 12, 8, "west", L >= 3), ("s", 12, 7, sl("spruce", "top")),
        ("o", 12, 7, "candle[candles=2,lit=false,waterlogged=false]"), ("rug", 10, 6, 11, 8, "brown_carpet"),
        ("s", 8, 5, "barrel[facing=up,open=false]"), ("L", 8, 7)], "spruce")
    if sto >= 2:
        # outside stair to the bedroom loft (cottage style): ladder in the corner
        for y in range(y0, 7):
            d.set(6 + 1, y, 9, "ladder[facing=east,waterlogged=false]") if False else None
        d.fill(7, 5, 8, 7, 5, 9, AIR)
        for y in range(y0, 7):
            d.set(7, y, 9, "ladder[facing=north,waterlogged=false]")
        d.set(7, 7, 9, AIR)
        d.set(7, 8, 9, AIR)
        n1 = JACK_RACKS[L] - racks if L < 3 else 1
        fit(d, 6, [("bed", 13, 9, "south"), ("s", 12, 9, sl("spruce", "top")),
                   ("o", 12, 9, "candle[candles=1,lit=false,waterlogged=false]"), ("r", 9, 9, 1),
                   ("s", 10, 9, "chest[facing=north,type=single,waterlogged=false]"), ("s", 8, 5, pot(2)),
                   ("rug", 10, 6, 12, 7, "red_carpet"), ("L", 12, 6)], "spruce")
        racks += n1
    if L >= 5:
        spot_trees(d, [(31, 2), (31, 8), (17, 2)], "oak", 4)
    # log store lean-to on the west wall
    for z in range(4, 11):
        for x in range(3, 6):
            d.set(x, 5, z, sl("spruce", "top" if x == 5 else "bottom"))
    for z in (4, 10):
        d.fill(3, y0, z, 3, 4, z, lg("stripped_dark_oak_log", "y"))
    log_pile(d, 3, 5, 5, 9, y0, 3, "oak_log", "z")
    chopping_block(d, 6, 13, y0)
    sawhorse(d, 9, 13, y0)
    flower_bed(d, 10, 2, 14, 2, y0, seed=1)
    for x in range(6, 16):
        if x != 9:
            d.set(x, y0, 1, "oak_fence")
    lamp_post(d, 16, 2, y0, P)
    # ---- log barn (L3+)
    if L >= 3:
        d.sty_over = dict(wall="spruce_planks", wall0="cobblestone", end="spruce_planks")
        b = build(d, 19, 4, 29, 14, 1, H=5, roof="gable", axis="z")
        d.sty_over = {}
        b.opening(23, 4, 25, 4, 4, lg("stripped_dark_oak_log", "x"))
        log_pile(d, 22, 8, 26, 10, y0, 2, "oak_log", "x")
        fit(d, y0, [("r", 20, z, 1) for z in (11, 12, 13)[:JACK_RACKS[L] - racks]] + [
            ("s", 27, 12, "chest[facing=west,type=single,waterlogged=false]"), ("s", 27, 13, "hay_block[axis=y]"),
            ("L", 24, 6), ("L", 24, 12)])
        racks = JACK_RACKS[L]
        wagon(d, 22, 16, y0, "oak", lg("oak_log", "x"))
    # ---- charcoal burner's hut with clamp + garden (L4+)
    if L >= 4:
        d.sty_over = dict(wall="mud_bricks", wall0="mud_bricks", end="mud_bricks")
        c = build(d, 3, 17, 11, 25, 2, roof="gable", axis="z", core=(9, 19), chimney=(4, 22, "east"))
        d.sty_over = {}
        c.door(8, 17, "north")
        # burner's hut: settle by the fire, coal sacks, the barrel and composter for the leaf litter
        fit(d, y0, [("i", 6, 24, "composter"), ("i", 7, 24, "barrel", "north"), ("s", 5, 18, "coal_block"),
                    ("s", 6, 18, "black_wool"), ("c", 6, 22, "east", False), ("L", 6, 20)], "spruce")
        fit(d, 6, [("bed", 6, 24, "south"), ("s", 7, 24, sl("spruce", "top")), ("s", 5, 18, "chest[facing=south,type=single,waterlogged=false]"),
                   ("s", 7, 18, pot(0)), ("L", 6, 23)], "spruce")
        # charcoal clamp: earth mound with smoke
        cx, cz = 16, 21
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                h = 2 - max(abs(dx), abs(dz)) + 1
                for k in range(h):
                    d.set(cx + dx, y0 + k, cz + dz, "coarse_dirt" if k < h - 1 else "podzol[snowy=false]")
        d.set(cx, y0 + 3, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        for x, z in ring(13, 24, 29, 28):
            d.set(x, y0, z, "oak_fence")
        d.set(21, y0, 24, AIR)
        for x in range(14, 29):
            for z in (26, 27):
                d.set(x, 1, z, "farmland[moisture=7]")
                d.set(x, y0, z, "oak_sapling[stage=0]" if x % 2 else "birch_sapling[stage=0]")
    # ---- timber storehouse (L5)
    if L >= 5:
        e = build(d, 19, 15, 29, 22, 3, roof="gable", axis="x", core=(20, 16))
        e.door(29, 18, "east", double=True)
        for s_ in (0, 1, 2):                                       # timber store floors
            yy = e.stand(s_)
            log_pile(d, 24, 19, 27, 20, yy, 2 if s_ < 2 else 1, "oak_log" if s_ == 0 else "stripped_oak_log", "x")
            fit(d, yy, [("s", 24, 17, "oak_planks"), ("s", 25, 17, "oak_planks"), ("o", 24, 17, sl("oak")),
                        ("L", 26, 18)])
        # hoist beam on the gable
        d.set(30, e.yr - 1, 18, lg("dark_oak_log", "x"))
        d.set(31, e.yr - 1, 18, lg("dark_oak_log", "x"))
        for y in range(e.yr - 4, e.yr - 1):
            d.set(31, y, 18, CHAIN)
        d.set(31, e.yr - 5, 18, lg("oak_log", "x"))
        hedge(d, [(0, z) for z in range(3, 29)], y0, "oak")
        for z in (8, 16, 24):
            lamp_post(d, 1, z, y0, P)
        tree(d, 2, 27, y0, "oak", 4, 1)
    return d


def jack_cas(rel, L):
    d = Design("Cascadia", rel, (30, 30, 41), paving="coarse_dirt")
    P, y0 = "Cascadia", 2
    sto = 1 if L == 1 else 2
    z2 = {1: 12, 2: 14}.get(L, 16)
    a = build(d, 5, 7, 15, z2, sto, roof="gable", axis="z", core=(13, 9) if sto > 1 else None,
              chimney=(10, z2 - 1, "north"))
    a.door(8, 7, "north")
    d.hut(6, y0, 8)
    # lodge room: settle facing the stone fireplace on the back wall, tool bench, gear racks; sleeping loft above
    fz = z2 - 1
    racks = min(JACK_RACKS[L], 3)
    fit(d, y0, [("i", 7, fz, "crafting_table", "north"), ("r", 6, 9, 1), ("r", 6, 10, 1)] +
        ([("r", 6, 11, 1)] if racks > 2 else []) +
        [("c", x, fz - 2, "north", False) for x in (9, 10, 11)] +
        [("s", 12, 8, "chest[facing=south,type=single,waterlogged=false]"), ("L", 9, 9)], "spruce")
    if sto >= 2:
        n1 = {2: 0, 3: 1, 4: 2, 5: 2}[L]
        fit(d, 6, [("bed", 7, fz, "south"), ("s", 8, fz, sl("spruce", "top")),
                   ("o", 8, fz, "candle[candles=1,lit=false,waterlogged=false]")] +
            [("r", 6, z, 1) for z in (9, 10)[:n1]] + [("s", 11, 8, "chest[facing=south,type=single,waterlogged=false]"),
                                                      ("L", 9, 9)], "spruce")
        racks += n1
    # front deck with railing
    for x in range(4, 17):
        for z in (3, 4, 5, 6):
            d.set(x, 1, z, "spruce_planks")
        if x not in (8,):
            d.set(x, y0, 3, "spruce_fence")
    for x in (4, 16):
        d.set(x, y0 + 1, 3, LANT_S)
    seats = 0
    if L >= 3:
        d.chair(11, y0, 5, "south", "spruce", arms=True)
        d.chair(13, y0, 5, "south", "spruce", arms=True)
        for x in range(4, 17):
            for z in (3, 4, 5, 6):
                d.set(x, 6, z, sl("mangrove"))
        for x in (4, 16):
            d.fill(x, y0, 3, x, 5, 3, lg("spruce_log", "y"))
        d.set(x, y0 + 1, 3, "spruce_fence")
    log_pile(d, 0, 9, 2, 17, y0, 3, "spruce_log", "z")
    chopping_block(d, 18, 9, y0, "spruce_log")
    sawhorse(d, 18, 12, y0, "spruce", "z")
    # ---- woodshed (L3+)
    if L >= 3:
        wx1, wx2, wz1, wz2 = 19, 25, 15, 21
        for x, z in ((wx1, wz1), (wx2, wz1), (wx1, wz2), (wx2, wz2)):
            d.fill(x, y0, z, x, 4, z, lg("spruce_log", "y"))
        for z in range(wz1 - 1, wz2 + 2):
            for x in range(wx1 - 1, wx2 + 2):
                d.set(x, 5, z, sl("mangrove"))
        log_pile(d, wx1 + 1, wz2, wx2 - 1, wz2, y0, 2, "spruce_log", "x")
        rack_line(d, [(wx2, wz1 + 2), (wx2, wz1 + 3)], y0, JACK_RACKS[L] - racks, 1, "west")
        racks = JACK_RACKS[L]
        if L >= 4:
            d.item(wx1 + 1, y0, wz1 + 1, "composter")
            d.item(wx1 + 2, y0, wz1 + 1, "barrel", "north")
            for x in range(wx1 + 4, wx2):
                d.set(x, 1, wz1 + 1, "podzol[snowy=false]")
                d.set(x, y0, wz1 + 1, "spruce_sapling[stage=0]")
    # ---- saw filer's shop (L3+)
    if L >= 3:
        f = build(d, 19, 23, 27, 29, 1, roof="gable", axis="x", chimney=(26, 26, "west"))
        f.door(22, 23, "north")
        fit(d, y0, [("s", 21, 28, "grindstone[face=floor,facing=north]"), ("s", 22, 28, "anvil[facing=east]"),
                    ("s", 23, 28, sl("spruce", "top")), ("o", 23, 28, "iron_bars"), ("c", 23, 27, "north", False),
                    ("s", 20, 24, "chest[facing=east,type=single,waterlogged=false]"), ("L", 21, 26)], "spruce")
        bench(d, 24, 22, y0, "south", 2, "spruce", sit=False)
    # ---- fire lookout tower (L4+)
    if L >= 4:
        tx, tz = 23, 4
        top = 16
        for x in (tx, tx + 4):
            for z in (tz, tz + 4):
                d.fill(x, y0, z, x, top, z, lg("spruce_log", "y"))
        for y in range(y0 + 3, top, 4):
            for k in range(5):
                d.set(tx + k, y, tz, lg("stripped_spruce_log", "x"))
                d.set(tx + k, y, tz + 4, lg("stripped_spruce_log", "x"))
                d.set(tx, y, tz + k, lg("stripped_spruce_log", "z"))
                d.set(tx + 4, y, tz + k, lg("stripped_spruce_log", "z"))
        for y in range(y0, top + 1):
            d.set(tx + 2, y, tz + 1, "ladder[facing=south,waterlogged=false]")
        d.fill(tx + 2, y0, tz, tx + 2, top, tz, "spruce_planks")
        # cab
        cy = top + 1
        d.fill(tx - 1, top, tz - 1, tx + 5, top, tz + 5, "spruce_planks")
        d.set(tx + 2, top, tz + 1, "ladder[facing=south,waterlogged=false]")
        for x, z in ring(tx - 1, tz - 1, tx + 5, tz + 5):
            d.set(x, cy, z, "spruce_planks")
            d.set(x, cy + 1, z, "glass_pane")
            d.set(x, cy + 2, z, "glass_pane")
        d.hip(tx - 1, tz - 1, tx + 5, tz + 5, cy + 3, "mangrove_stairs", "mangrove_slab")
        d.set(tx + 2, cy + 2, tz + 2, LANT)
        d.set(tx + 2, cy, tz + 3, sl("spruce", "top"))
        d.set(tx + 2, cy + 1, tz + 3, "cartography_table") if False else None
        d.chair(tx + 3, cy, tz + 3, "east", "spruce", sit=False)
    # ---- crew bunkhouse (L4+)
    if L >= 4:
        e = build(d, 4, 21, 16, 29, 2, roof="gable", axis="x", core=(14, 23), chimney=(5, 25, "east"))
        e.door(9, 21, "north")
        fit(d, y0, [("c", 7, z, "east", False) for z in (24, 25, 26)] + [
            ("s", 10, 27, "spruce_fence"), ("o", 10, 27, "spruce_pressure_plate[powered=false]"),
            ("c", 9, 27, "west", False), ("c", 11, 27, "east", False), ("rug", 6, 24, 6, 26, "green_carpet"),
            ("s", 12, 22, "barrel[facing=south,open=false]"), ("L", 10, 24)], "spruce")
        fit(d, 6, [("bed", x, 28, "south") for x in (7, 9, 11)] + [("s", 8, 28, sl("spruce", "top")),
                                                                    ("s", 10, 28, sl("spruce", "top")),
                                                                    ("s", 12, 22, "chest[facing=south,type=single,waterlogged=false]"),
                                                                    ("L", 10, 25)], "spruce")
    # ---- cookhouse / mess hall (L5)
    if L >= 5:
        m = build(d, 4, 33, 20, 40, 3, roof="gable", axis="x", core=(18, 35), chimney=(5, 36, "east"))
        m.door(11, 33, "north", double=True)
        fit(d, y0, [("s", 8, 39, "smoker[facing=north,lit=false]"), ("s", 9, 39, sl("spruce", "top")),
                    ("s", 10, 39, "water_cauldron[level=3]"), ("s", 11, 39, "furnace[facing=north,lit=false]")] +
            [("s", x, 36, sl("spruce", "top")) for x in range(9, 15)] +
            [("c", x, 35, "north", False) for x in range(9, 15)] + [("c", x, 37, "south", False) for x in range(9, 15)] +
            [("L", 11, 35), ("L", 14, 38)], "spruce")
        fit(d, 6, [("bed", x, 39, "south") for x in (7, 9, 11, 13)] + [("s", 15, 39, "chest[facing=north,type=single,waterlogged=false]"),
                                                                        ("L", 10, 36)], "spruce")
        fit(d, 10, [("s", 7, 39, "hay_block[axis=y]"), ("s", 8, 39, "white_wool"), ("s", 9, 39, "brown_wool"),
                    ("o", 7, 39, "hay_block[axis=y]"), ("L", 10, 36)])
    tree(d, 27, 37 if L >= 3 else 28, y0, "spruce", 6, 2)
    tree(d, 1, 26, y0, "spruce", 5, 2) if L < 4 else None
    return d


@design("lumberjack")
def lumberjack(pack, rel, L):
    return demote({"Neoterra": jack_neo, "Hearthwood": jack_hw, "Cascadia": jack_cas}[pack](rel, L), L)


# =============================================================================================== FLETCHER
"""
Fletcher
  Neoterra   "Archery centre" (light-grey concrete, white fins, magenta bands): arrow studio (bow lab upstairs from
             L2) with a glazed outdoor shooting lane; indoor range hall with lanes and targets (L3); pro shop and
             spectators' gallery (L4); clubhouse tower with a roof deck (L5).
  Hearthwood "The Bow & Quiver" (yellow colour-washed plaster, oak framing, brown tile roofs, crimson shutters):
             bowyer's shop with a hanging sign (upper workroom from L2), garden lane with straw butts; stave
             drying barn (L3); fletcher's cottage and archery field pavilion (L4); archers' guildhall (L5).
  Cascadia   "Bowyer's cabin" (pale birch board-and-batten, slate roofs, forest-green trim): cabin with a side
             porch as the shooting line of a long range (loft from L2); stave shed (L3); range clubhouse (L4);
             hunting lodge with a trophy hall (L5).
"""
FLETCH = {1: 2, 2: 3, 3: 4, 4: 5, 5: 5}
FRACKS = {1: 2, 2: 3, 3: 4, 4: 5, 5: 6}


def butt(d, x, z, y, facing, target=True, w=2):
    """Straw archery butt: hay bales with target faces (the first is the counted yard target)."""
    dx, dz = (1, 0) if facing in ("north", "south") else (0, 1)
    for k in range(w):
        cx, cz = x + dx * k, z + dz * k
        d.set(cx, y, cz, "hay_block[axis=y]")
        if k == 0 and target:
            d.yard_item(cx, y + 1, cz, "target[power=0]")
        else:
            d.set(cx, y + 1, cz, "target[power=0]" if k % 2 == 0 else "hay_block[axis=y]")


def range_lanes(d, x1, z1, x2, z2, y, facing="south", wood="spruce", every=3, light=True):
    """Shooting lanes inside a hall: hay backstop wall at the far end with targets, lane dividers (fences)."""
    if facing == "south":
        for x in range(x1, x2 + 1):
            d.set(x, y, z2, "hay_block[axis=x]")
            d.set(x, y + 1, z2, "target[power=0]" if (x - x1) % every == 1 else "hay_block[axis=x]")
            d.set(x, y + 2, z2, "hay_block[axis=x]")
        for x in range(x1 + every - 1, x2, every):
            for z in range(z1 + 3, z2 - 1, 1):
                d.set(x, y - 1, z, "white_concrete" if wood == "birch" else "stripped_spruce_wood[axis=y]")
        for x in range(x1, x2 + 1):
            d.set(x, y, z1 + 1, sl(wood, "top") if (x - x1) % every != 1 else AIR)


def fl_neo(rel, L):
    d = Design("Neoterra", rel, (36, 26, 34), paving="smooth_stone")
    P, y0 = "Neoterra", 2
    sto = 1 if L == 1 else 2
    a = build(d, 3, 4, 13, 12, sto, roof="flat", core=(11, 6) if sto > 1 else None, street_glass=True)
    a.door(6, 4, "north", double=True)
    d.hut(4, y0, 5)
    d.sign(9, 5, 3, "north", ["ARROW", "STUDIO"], "birch", glow=True, color="magenta")
    # studio: fletching benches on the back wall, arrow racks, bow lab upstairs with the arrow stock barrels
    racks = min(FRACKS[L], 3)
    furnish(a.room(0, back="south"), "workshop", ["crafting_table"] + ["fletching_table"] * min(FLETCH[L], 3),
            racks=racks)
    if sto >= 2:
        up = ["fletching_table"] * max(0, FLETCH[L] - 3) + (["barrel"] * 5 if L >= 3 else [])
        furnish(a.room(1, back="south"), "workshop", up, racks=FRACKS[L] - racks)
        racks = FRACKS[L]
    neo_roof(d, a, [(5, 11, 6, SOLAR), (5, 11, 9, SOLAR)])
    if L >= 5:
        spot_trees(d, [(1, 30), (14, 32), (22, 30)], "birch", 3)
    # glazed outdoor lane east of the studio
    lx1, lx2 = 16, 20
    d.fill(lx1, 1, 4, lx2, 1, 22, "grass_block[snowy=false]")
    for z in range(4, 23):
        for x in (lx1 - 1, lx2 + 1):
            d.set(x, y0, z, "light_gray_concrete")
            d.set(x, y0 + 1, z, "glass_pane")
            d.set(x, 1, z, "smooth_stone")
    for x in range(lx1 - 1, lx2 + 2):
        d.set(x, y0, 23, "hay_block[axis=x]")
        d.set(x, y0 + 1, 23, "hay_block[axis=x]")
        d.set(x, y0, 7, sl("smooth_quartz", "top")) if x != 18 else None
        for z in range(4, 7):
            d.set(x, 5, z, sl("smooth_quartz", "top"))
    butt(d, lx1, 22, y0, "north")
    butt(d, lx2 - 1, 22, y0, "north", target=False)
    for x in (lx1, lx2):
        d.set(x, 4, 5, SLANT)
    lamp_post(d, 14, 2, y0, P)
    for x in (1, 22):
        d.set(x, y0, 3, "moss_block")
        tree(d, x, 3, y0 + 1, "birch", 3, 1)
    if L >= 2:
        bench(d, 4, 2, y0, "north", 2, "birch", sit=False)
        for z in range(5, 12):
            d.set(1, y0, z, "moss_block")
            d.set(1, y0 + 1, z, "azalea" if z % 2 else "fern")
    # ---- indoor range hall (L3+)
    if L >= 3:
        h = build(d, 3, 15, 13, 32, 1, H=5, roof="flat")
        h.door(8, 15, "north", double=True)
        range_lanes(d, 4, 16, 12, 31, y0, "south", "birch")
        rh = h.room(0)
        rh.keep |= {(x, z) for x in range(4, 13) for z in range(16, 32)}
        for x in (5, 8, 11):
            d.set(x, 5, 24, "sea_lantern")
        neo_roof(d, h, [(5, 11, 17, SOLAR), (5, 11, 20, SOLAR), (5, 11, 23, SOLAR), (5, 11, 26, SOLAR), (5, 11, 29, SOLAR)])
    # ---- pro shop + gallery (L4+)
    if L >= 4:
        c = build(d, 23, 4, 33, 12, 3, roof="flat", core=(31, 6), street_glass=True)
        c.door(26, 4, "north", double=True)
        furnish(c.room(0, back="south"), "shop")                       # pro shop counter
        furnish(c.room(1, back="south"), "lounge", seats=4, sit=False)
        furnish(c.room(2, back="south"), "office", seats=3, sit=False)   # spectators' gallery desks
        neo_roof(d, c, [(25, 29, 6, MOSS), (25, 29, 7, 'azalea'), (25, 29, 9, MOSS), (25, 29, 10, 'azalea')])
        d.sign(28, 6, 3, "north", ["PRO SHOP", "BOWS & GEAR"], "birch", glow=True, color="magenta")
    # ---- clubhouse tower (L5)
    if L >= 5:
        t = build(d, 23, 16, 33, 24, 4, roof="flat", core=(31, 18))
        t.door(26, 16, "north")
        for s_, kind in enumerate(("kiosk", "canteen", "library", "lounge")):    # clubhouse floors
            furnish(t.room(s_, back="south"), kind, books=8 if kind == "library" else 0, sit=False,
                    seats=2 if kind == "lounge" else 0)
        neo_roof(d, t, [(25, 29, 18, MOSS), (25, 29, 19, 'azalea'), (25, 29, 21, MOSS), (25, 29, 22, 'azalea')])
        for z in (14, 26, 30):
            lamp_post(d, 34, z, y0, P)
        for x in range(23, 34, 2):
            d.set(x, t.yr + 3, 16, "magenta_stained_glass") if False else None
    return d


def fl_hw(rel, L):
    d = Design("Hearthwood", rel, (34, 22, 34), paving="gravel")
    P, y0 = "Hearthwood", 2
    sto = 1 if L == 1 else 2
    a = build(d, 4, 4, 14, 11, sto, roof="gable", axis="x", core=(12, 5) if False else None,
              chimney=(5, 8, "east"))
    a.door(11, 4, "north")
    d.hut(5, y0, 5)
    d.sign(12, 4, 3, "north", ["The Bow", "& Quiver"], "oak", hanging=True)
    # bay shop window with bows on display
    for x in range(7, 10):
        d.set(x, y0, 3, "oak_planks")
        d.window(x, 3, 3, x, 4, 3)
        d.set(x, 5, 3, sl("mud_brick"))
    for x in range(7, 10):                                          # display shelf in the bay window
        d.set(x, 3, 4, AIR)
        d.set(x, 4, 4, AIR)
        d.set(x, y0, 4, sl("oak", "top"))
        d.set(x, y0 + 1, 4, "bow" if False else _pot(x))
    racks = min(FRACKS[L], 2)
    furnish(a.room(0, back="south"), "workshop", ["crafting_table"] + ["fletching_table"] * min(FLETCH[L], 3),
            racks=racks, wood="oak")
    if sto >= 2:
        for y in range(y0, 7):
            d.set(13, y, 10, "ladder[facing=north,waterlogged=false]")
        d.set(13, 7, 10, AIR)
        d.set(13, 8, 10, AIR)
        n1 = FRACKS[L] - racks if L < 3 else 1
        furnish(a.room(1, back="north"), "workshop", ["fletching_table"] * max(0, FLETCH[L] - 3), racks=n1,
                wood="oak")
        racks += n1
    if L >= 2:
        lamp_post(d, 2, 2, y0, P)
    # garden lane with straw butts behind
    gz1, gz2 = 13, 26
    for x, z in ring(2, gz1, 16, gz2):
        if z == gz1 and 4 <= x <= 14:
            continue
        d.set(x, y0, z, "oak_fence")
    d.set(2, y0, gz1 + 2, AIR)
    d.fill(6, 1, gz1, 11, 1, gz2 - 1, "grass_block[snowy=false]")
    butt(d, 6, gz2 - 2, y0, "north")
    butt(d, 9, gz2 - 2, y0, "north", target=False)
    for x in range(6, 12):
        d.set(x, 1, gz1 + 2, "stone_bricks")
    flower_bed(d, 3, gz1 + 1, 4, gz2 - 2, y0, seed=2)
    flower_bed(d, 13, gz1 + 1, 15, gz2 - 2, y0, seed=5)
    flower_bed(d, 4, 1, 6, 1, y0, seed=1)
    lamp_post(d, 15, 2, y0, P)
    # ---- stave drying barn (L3+)
    if L >= 3:
        d.sty_over = dict(wall="oak_planks", wall0="bricks", end="oak_planks")
        b = build(d, 19, 4, 27, 13, 1, H=5, roof="gable", axis="z")
        d.sty_over = {}
        b.door(23, 4, "north", double=True)
        furnish(b.room(0, back="south"), "loft", ["barrel"] * 5, racks=FRACKS[L] - racks)   # stave store
        racks = FRACKS[L]
    # ---- fletcher's cottage & field pavilion (L4+)
    if L >= 4:
        c = build(d, 19, 17, 29, 24, 2, roof="gable", axis="x", core=(27, 18), chimney=(20, 21, "east"))
        c.door(23, 17, "north")
        furnish(c.room(0, back="west"), "lounge", wood="oak")          # parlour round the hearth
        furnish(c.room(1, back="south"), "dorm", beds=1, wood="oak")
        # open pavilion at the butts end
        for x, z in ((3, 28), (9, 28), (3, 32), (9, 32)):
            d.fill(x, y0, z, x, 4, z, lg("stripped_oak_log", "y"))
        d.hip(3, 28, 9, 32, 5, "mud_brick_stairs", "mud_brick_slab", overhang=0)
        bench(d, 5, 30, y0, "south", 3, "oak", sit=False)
    # ---- archers' guildhall (L5)
    if L >= 5:
        g = build(d, 13, 27, 31, 33, 2, roof="gable", axis="x", core=(29, 28), chimney=(14, 30, "east"))
        g.door(20, 27, "north", double=True)
        furnish(g.room(0, back="south"), "canteen", sit=False, wood="oak")       # guild feast hall
        furnish(g.room(1, back="south"), "library", books=8, seats=2, sit=False, wood="oak")
        for x in (31, 33):
            for z in (6, 12, 18):
                lamp_post(d, x, z, y0, P) if x == 31 else tree(d, x, z, y0, "oak", 4, 1)
        for z in (24, 30):
            lamp_post(d, 33, z, y0, P)
        tree(d, 1, 30, y0, "oak", 4, 1)
    return d


def fl_cas(rel, L):
    d = Design("Cascadia", rel, (36, 22, 34), paving="coarse_dirt")
    P, y0 = "Cascadia", 2
    sto = 1 if L == 1 else 2
    a = build(d, 3, 5, 11, 13, sto, roof="gable", axis="z", core=(4, 7) if sto > 1 else None)
    a.door(7, 5, "north")
    a.door(11, 11, "east")
    d.sign(7, 5, 4, "north", ["BOWS", "& ARROWS"], "spruce") if False else None
    d.sign(9, 5, 4, "north", ["BOWS", "& ARROWS"], "spruce")
    d.hut(10, y0, 6)
    racks = 2 if L == 1 else 0
    furnish(a.room(0, back="south"), "workshop", ["crafting_table"] + ["fletching_table"] * min(FLETCH[L], 2),
            racks=racks)
    if sto >= 2:                                                     # loft: more benches, racks and the bunk
        n1 = FRACKS[L] if L < 3 else 2
        furnish(a.room(1, back="south"), "dorm", ["fletching_table"] * max(0, FLETCH[L] - 2), racks=n1, beds=1)
        racks += n1
    # side porch = shooting line, range to the east with a hay-bale berm
    for x in range(12, 15):
        for z in range(5, 14):
            d.set(x, 1, z, "spruce_planks")
            d.set(x, 6, z, sl("dark_oak", "top" if x == 12 else "bottom"))
    for z in (5, 13):
        d.fill(14, y0, z, 14, 5, z, lg("spruce_log", "y"))
    for z in range(6, 13):
        if z not in (9, 10, 11):
            d.set(14, y0, z, "spruce_fence")
    rz1, rz2 = 7, 12
    for x in range(15, 33):
        for z in (rz1 - 1, rz2 + 1):
            d.set(x, y0, z, "spruce_fence")
    for z in range(rz1 - 1, rz2 + 2):
        for y in (y0, y0 + 1, y0 + 2):
            d.set(33, y, z, "hay_block[axis=z]")
    butt(d, 32, rz1 + 1, y0, "west", w=1)
    d.set(32, y0, rz2 - 1, "hay_block[axis=y]")
    d.set(32, y0 + 1, rz2 - 1, "target[power=0]")
    for x in range(16, 32, 4):
        d.set(x, y0 + 1, rz1 - 1, "torch")
    lamp_post(d, 2, 3, y0, P)
    if L >= 2:
        bench(d, 4, 3, y0, "north", 2, "spruce", sit=False)
        log_pile(d, 0, 6, 1, 13, y0, 2, "spruce_log", "z")
    # ---- stave & feather shed (L3+)
    if L >= 3:
        d.sty_over = dict(wall="spruce_planks", wall0="spruce_planks", end="spruce_planks")
        sb = build(d, 3, 16, 12, 22, 1, H=5, roof="gable", axis="x")
        d.sty_over = {}
        sb.door(7, 16, "north", double=True)
        furnish(sb.room(0, back="south"), "store", ["barrel"] * 5, racks=FRACKS[L] - racks)
        racks = FRACKS[L]
        wagon(d, 14, 17, y0, "spruce", "hay_block[axis=z]", "z")
        for x in (1, 13):
            lamp_post(d, x, 23, y0, P)
        log_pile(d, 0, 16, 1, 22, y0, 2, "stripped_spruce_log", "z")
        tree(d, 2, 26, y0, "spruce", 5, 1) if L < 5 else None
        tree(d, 14, 26, y0, "spruce", 5, 1) if L < 5 else tree(d, 34, 24, y0, "spruce", 5, 1)
    # ---- range clubhouse (L4+)
    if L >= 4:
        c = build(d, 16, 15, 26, 23, 2, roof="gable", axis="x", core=(24, 16), chimney=(17, 19, "east"))
        c.door(20, 15, "north", double=True)
        furnish(c.room(0, back="west"), "lounge", seats=3, sit=False)    # clubhouse fireside
        furnish(c.room(1, back="south"), "office", seats=2, sit=False)
        bench(d, 16, 14, y0, "south", 2, "spruce", sit=False) if False else None
    # ---- hunting lodge (L5)
    if L >= 5:
        e = build(d, 3, 25, 26, 33, 2, roof="gable", axis="x", core=(24, 27), chimney=(4, 29, "east"))
        e.door(14, 25, "north", double=True)
        furnish(e.room(0, back="south"), "canteen", sit=False)           # trophy hall dining
        furnish(e.room(1, back="south"), "dorm", beds=4, racks=FRACKS[L] - racks)
        racks = FRACKS[L]
        tree(d, 33, 30, y0, "spruce", 6, 2)
    else:
        tree(d, 30, 28, y0, "spruce", 6, 2)
    return d


@design("fletcher")
def fletcher(pack, rel, L):
    return demote({"Neoterra": fl_neo, "Hearthwood": fl_hw, "Cascadia": fl_cas}[pack](rel, L), L)


# =============================================================================================== WAREHOUSE
"""
Warehouse
  Neoterra   "Logistics hub" (light-grey concrete over deepslate cladding, yellow bands): racked storage hall that
             lengthens (L2), gains racked upper floors (L3, L5) with a stair core and front office strip; a
             two-storey dispatch & cold-store block with loading canopy (L4, 3 storeys at L5); truck bay, solar roofs.
  Hearthwood "Tithe barn" (Cotswold sandstone, stone plinth, blue-slate roofs): long stone barn with buttresses,
             gable to the street with a cart porch and nave + cross-aisle rack bays, lengthening each level;
             steward's house (L3), granary loft barn (L4), second barn closing the yard (L5).
  Cascadia   "Freight depot" (red mangrove siding, dark shake roofs, mustard trim): depot on a raised dock with rail
             siding that grows along the track; freight agent's office (L3); upper rack loft (L4); second depot
             shed and team stable (L5).
"""
WH = {1: 36, 2: 72, 3: 144, 4: 216, 5: 324}


def wh_list(L, first=True):
    """Warehouse work blocks for the clerk's office."""
    return (["crafting_table"] if first else []) + (["crafting_table", "cartography_table", "lectern"] +
                                                    ["barrel"] * 4 if L >= 3 else []) + \
        (["ender_chest"] if L >= 5 else [])


def wh_racks(d, y, x1, z1, x2, z2, need, along="z"):
    """Rack aisles over the rectangle given for that floor (row start, double rows, 1-wide walkways)."""
    return aisles(d, x1, z1, x2, z2, y, need, 3, along)


def wh_neo(rel, L):
    d = Design("Neoterra", rel, (36, 22, 26), paving="smooth_stone")
    P, y0 = "Neoterra", 2
    sto = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3}[L]
    z2 = 12 if L == 1 else 18
    a = build(d, 3, 4, 17, z2, sto, H=5 if sto == 1 else 4, roof="flat", core=(15, 10) if sto > 1 else None,
              street_glass=True)
    a.door(6, 4, "north", double=True)
    a.opening(10, 4, 12, 4, 3, "yellow_concrete")
    d.hut(4, y0, 5)
    d.sign(10, a.yr, 3, "north", ["NEOTERRA", "LOGISTICS"], "birch", glow=True, color="yellow")
    r0 = a.room(0, back="north")
    racks = wh_racks(d, r0, 4, 10, 13, z2 - 1, WH[L] if L == 1 else max(WH[L], 144))
    ups = []
    for s_ in range(1, sto):
        rs = a.room(s_, back="north")
        racks += wh_racks(d, rs, 4, 10, 13, z2 - 1, max(108, WH[L] - racks))
        ups.append(rs)
    # goods-in desk on the ground floor; the clerk's office on the first floor front
    furnish(r0, "shop", ["crafting_table"])
    if ups:
        furnish(ups[0], "office", wh_list(L, first=False), seats=2 if L >= 3 else 0)
        for rs in ups[1:]:
            furnish(rs, "loft")
    neo_roof(d, a, [(5, 13, 6, SOLAR), (5, 13, 9, SOLAR)] + ([(5, 13, 12, SOLAR), (5, 13, 15, SOLAR)] if z2 > 12 else []))
    # truck bay with markings and pallets
    for x in range(10, 13):
        for z in range(0, 4):
            d.set(x, 1, z, "yellow_concrete" if z % 2 else "black_concrete")
    for x in (1, 19):
        d.set(x, y0, 3, "moss_block")
        tree(d, x, 3, y0 + 1, "birch", 3, 1)
    lamp_post(d, 8, 1, y0, P)
    for z in range(5, z2, 3):
        crate_stack(d, 19, z, y0, 2)
    if L >= 2:
        bench(d, 4, 2, y0, "north", 2, "birch", sit=False)
        for z in range(5, z2):
            d.set(1, y0, z, "moss_block")
            d.set(1, y0 + 1, z, "azalea" if z % 2 else "fern")
    # ---- dispatch & cold store block (L4+)
    if L >= 4:
        bs = 2 if L == 4 else 3
        b = build(d, 21, 4, 33, 14, bs, roof="flat", core=(31, 6), street_glass=True)
        b.door(24, 4, "north", double=True)
        rb = b.room(0, back="north")
        racks += wh_racks(d, rb, 22, 9, 28, 13, max(36, WH[L] - racks))
        furnish(rb, "shop")                                          # dispatch counter
        for s_ in range(1, bs):
            rr = b.room(s_, back="north")
            if s_ == 1:
                furnish(rr, "canteen", sit=False)                    # drivers' canteen
            else:
                racks += wh_racks(d, rr, 22, 9, 28, 13, max(36, WH[L] - racks))
                furnish(rr, "office", seats=2, sit=False)
        neo_roof(d, b, [(23, 29, 6, MOSS), (23, 29, 8, 'azalea'), (23, 29, 10, MOSS), (23, 29, 12, 'azalea')])
        # loading canopy
        for x in range(21, 34):
            for z in range(16, 22):
                d.set(x, 6, z, sl("smooth_quartz", "top") if z < 21 else "yellow_concrete")
        for x in (21, 27, 33):
            d.fill(x, y0, 21, x, 5, 21, "polished_deepslate")
        for x in range(22, 33, 3):
            crate_stack(d, x, 18, y0, 2)
    if L >= 5:                                                       # weighbridge kiosk at the truck gate
        k = build(d, 3, 21, 9, 25, 2, roof="flat")
        k.door(6, 21, "north")
        furnish(k.room(0, back="south"), "kiosk", sit=False)
        furnish(k.room(1, back="south"), "office", seats=1, sit=False)
        for x in range(11, 19):
            for z in range(21, 25):
                d.set(x, 1, z, "iron_block" if z in (22, 23) else "yellow_concrete")
        d.fill(10, y0, 21, 10, 4, 21, "yellow_concrete")
        for x in range(10, 20):
            d.set(x, 5, 21, "yellow_concrete" if x % 2 else "black_concrete")
        neo_roof(d, k, [(5, 7, 23, SOLAR)])
        for x in (21, 27, 33):
            lamp_post(d, x, 24, y0, P)
    return d


def barn_bays(d, y, x1, x2, nave, z0, units, need):
    """Tithe-barn storage: double rows of rack columns across the barn either side of the given nave, a cross
    aisle after every pair, starting at row z0. Returns racks placed."""
    n = 0
    for u in range(units):
        za = z0 + 3 * u
        for z in (za, za + 1):
            for x in list(range(x1, nave[0])) + list(range(nave[1] + 1, x2 + 1)):
                if n < need:
                    n += rack_col(d, x, z, y)
    return n


def buttresses(d, b, mat="stone_bricks", stair="stone_brick"):
    for z in range(b.z1 + 3, b.z2, 3):
        for x, f in ((b.x1 - 1, "east"), (b.x2 + 1, "west")):
            if d.bp.inside(x, 2, z):
                d.fill(x, 2, z, x, 4, z, mat)
                d.set(x, 5, z, st(stair, f))


def wh_hw(rel, L):
    d = Design("Hearthwood", rel, (34, 26, 40), paving="gravel")
    P, y0 = "Hearthwood", 2
    U = L
    z2 = 9 + 3 * U
    a = build(d, 3, 4, 17, z2, 1, H=6 if L > 1 else 5, roof="gable", axis="z")
    buttresses(d, a, "sandstone", "sandstone")
    # cart porch (midstrey) from L2
    for z in (range(1, 4) if L >= 2 else ()):
        for y in range(y0, 6):
            d.set(8, y, z, "sandstone")
            d.set(12, y, z, "sandstone")
        for x in range(9, 12):
            d.set(x, 1, z, "spruce_planks")
    a.opening(9, 4, 11, 4, 4 if L > 1 else 3, lg("stripped_spruce_log", "x"))
    if L >= 2:
        d.gable(8, 1, 12, 3, 6, "z", "dark_prismarine_stairs", "dark_prismarine_slab", "smooth_sandstone", overhang=0)
        for x in range(9, 12):
            for y in range(y0, 6):
                d.set(x, y, 1, AIR)
            d.set(x, 6, 1, lg("stripped_spruce_log", "x"))
    d.sign(7, 4, 0, "north", ["Tithe Barn", "Stores"], "spruce") if False else None
    d.sign(13, 4, 3, "north", ["Tithe Barn", "Stores"], "spruce")
    d.hut(4, y0, 5)
    r0 = a.room(0, back="north")
    racks = barn_bays(d, r0, 4, 16, (9, 11), 9, U, WH[L])
    furnish(r0, "loft", ["crafting_table"], lights=False)          # sacks and hay at the threshing floor
    for z in range(9, z2, 3):
        d.set(10, 6, z, LANT)
    for x in (1, 19):
        lamp_post(d, x, 1, y0, P)
    flower_bed(d, 3, 1, 6, 2, y0, seed=2)
    flower_bed(d, 14, 1, 17, 2, y0, seed=3)
    # ---- steward's house (L2 cottage, two storeys from L3)
    if L >= 2:
        d.sty_over = dict(wall="calcite", wall0="sandstone", post="stripped_spruce_log[axis=y]")
        b = build(d, 21, 4, 31, 11, 2 if L >= 3 else 1, roof="gable", axis="x", core=(29, 5) if L >= 3 else None,
                  chimney=(22, 8, "east"))
        d.sty_over = {}
        b.door(25, 4, "north")
        if L >= 3:                                                   # steward's office and his chamber over it
            furnish_all([(b.room(0, back="south"), "office"), (b.room(1, back="south"), "office"),
                         (b.room(1, back="north"), "dorm")], items=wh_list(L, first=False), seats=2, beds=1)
        else:
            furnish(b.room(0, back="west"), "lounge")               # cottage parlour by the hearth
        for x in range(21, 32):
            if x != 25:
                d.set(x, y0, 2, "spruce_fence")
        flower_bed(d, 22, 3, 23, 3, y0, seed=6)
    # ---- granary on staddle stones (L3+)
    if L >= 3:
        for x in (21, 25):
            for z in (14, 18):
                d.set(x, y0, z, "stone_brick_wall")
                d.set(x, y0 + 1, z, "smooth_stone_slab[type=bottom,waterlogged=false]") if False else None
        d.fill(21, 3, 14, 25, 3, 18, "spruce_planks")
        for x, z in ring(21, 14, 25, 18):
            d.fill(x, 4, z, x, 6, z, "spruce_planks" if (x + z) % 2 else lg("stripped_spruce_log", "y"))
        d.gable(21, 14, 25, 18, 7, "x", "dark_prismarine_stairs", "dark_prismarine_slab", "spruce_planks")
        run_stairs(d, 23, 11, y0, 2, "south", "spruce") if False else None
        d.set(23, 4, 14, "spruce_door[facing=north,half=lower,hinge=left,open=false,powered=false]")
        d.set(23, 5, 14, "spruce_door[facing=north,half=upper,hinge=left,open=false,powered=false]")
        d.set(23, 3, 13, sl("spruce", "top"))
        d.set(23, y0, 12, st("spruce", "south"))
        hedge(d, [(0, z) for z in range(3, 38)], y0, "oak")
        for z in (8, 20, 32):
            lamp_post(d, 1, z, y0, P)
        tree(d, 32, 4, y0, "oak", 4, 1)
    # ---- granary loft barn (L4+)
    if L >= 4:
        g = build(d, 21, 20, 31, 30, 2, roof="gable", axis="z", core=(29, 22))
        buttresses(d, g, "sandstone", "sandstone")
        g.opening(25, 20, 26, 20, 3, lg("stripped_spruce_log", "x"))
        for s_ in (0, 1):
            rg = g.room(s_, back="north")
            racks += wh_racks(d, rg, 22, 23, 27, 29, max(36, WH[L] - racks))
            furnish(rg, "loft")
    # ---- second barn closing the yard (L5)
    if L >= 5:
        e = build(d, 3, 29, 17, 38, 2, roof="gable", axis="x", core=(15, 31))
        buttresses(d, e, "sandstone", "sandstone")
        e.opening(7, 29, 9, 29, 3, lg("stripped_spruce_log", "x"))
        for s_ in (0, 1):
            re = e.room(s_, back="north")
            racks += wh_racks(d, re, 4, 32, 13, 37, max(36, WH[L] - racks), "x")
            furnish(re, "loft")
        wagon(d, 19, 33, y0, "spruce", "hay_block[axis=z]", "z")
        # yard wall with a gateway between the barns
        for x in range(18, 33):
            if x not in (19, 20):
                d.set(x, y0, 39, "sandstone_wall")
        for z in range(31, 40):
            d.set(33, y0, z, "sandstone_wall")
        for x in (22, 26):
            for z in (33, 36):
                tree(d, x, z, y0, "oak", 4, 1)
        # dovecote
        for x, z in ring(29, 32, 32, 35):
            d.fill(x, y0, z, x, 7, z, "sandstone" if (x + z) % 3 else "smooth_sandstone")
            for y in (4, 6):
                if (x + z + y) % 2 and (x, z) not in ((29, 32), (32, 32), (29, 35), (32, 35)):
                    d.set(x, y, z, "spruce_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]") if False else None
        d.door(30, y0, 32, "north", "spruce")
        d.hip(29, 32, 32, 35, 8, "dark_prismarine_stairs", "dark_prismarine_slab")
        hedge(d, [(33, z) for z in range(14, 30)], y0, "oak")
        for z in (14, 22):
            lamp_post(d, 32, z, y0, P)
        for x in (19, 33):
            tree(d, x, 1, y0, "oak", 4, 1)
        lamp_post(d, 20, 0, y0, P)
        flower_bed(d, 22, 26, 23, 30, y0, seed=7) if False else None
        d.set(30, 7, 33, LANT) if False else None
    return d


def wh_cas(rel, L):
    d = Design("Cascadia", rel, (40, 24, 44), paving="coarse_dirt")
    P, y0 = "Cascadia", 3
    U = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5}[L]
    sto = 1 if L < 4 else 2
    x2 = 9 + 3 * U + 1
    zb = {1: 14, 2: 16}.get(L, 19)
    a = build(d, 3, 6, x2, zb, sto, H=5 if sto == 1 else 4, roof="gable", axis="x", y0=y0,
              core=(4, 12) if sto > 1 else None)
    d.fill(3, 2, 6, x2, 2, zb, "spruce_planks")
    for x, z in ring(3, 6, x2, zb):
        d.set(x, 2, z, "cobblestone" if (x + z) % 4 else "mossy_cobblestone")
    # dock with canopy, steps, rail siding
    for x in range(3, x2 + 1):
        for z in range(2, 6):
            d.set(x, 1, z, "cobblestone")
            d.set(x, 2, z, "spruce_planks")
        if L >= 2:
            d.set(x, 7, 1, st("cobbled_deepslate", "south"))
            for z in range(2, 6):
                d.set(x, 7, z, sl("cobbled_deepslate", "bottom" if z < 4 else "top"))
    for x in (range(3, x2 + 1, 4) if L >= 2 else ()):
        d.fill(x, y0, 2, x, 6, 2, lg("spruce_log", "y"))
    d.set(2, 2, 3, st("spruce", "east"))
    d.set(2, 2, 4, st("spruce", "east"))
    for x in range(0, d.sx):
        d.set(x, 1, 0, "gravel")
        d.set(x, 2, 0, "rail[shape=east_west,waterlogged=false]")
    a.door(5, 6, "north")
    for u in range(U):
        ax = 11 + 3 * u
        a.opening(ax, 6, ax, 6, 3, "yellow_terracotta")
    d.sign(7, 6, 5, "north", ["FREIGHT", "DEPOT"], "spruce")
    d.hut(4, y0, 7)
    r0 = a.room(0, back="west")
    racks = wh_racks(d, r0, 8, 8, x2 - 1, zb - 1, WH[L])
    furnish(r0, "shop", ["crafting_table"])                       # tally desk by the office door
    if sto > 1:
        r1 = a.room(1, back="west")
        racks += wh_racks(d, r1, 8, 8, x2 - 1, zb - 1, max(66, WH[L] - racks))
        furnish(r1, "loft")
    crate_stack(d, x2 - 1, 3, y0, 2)
    d.set(x2 - 2, y0, 3, "hay_block[axis=x]")
    lamp_post(d, 1, 7, 2, P)
    # ---- freight agent's office (L2, two storeys from L3)
    if L >= 2:
        b = build(d, 26, 2, 34, 10, 2 if L >= 3 else 1, roof="gable", axis="z", core=(32, 4) if L >= 3 else None)
        for x in range(25, 36):
            for y in range(2, b.ridge + 2):
                if y >= b.yr or x in (25, 35):
                    d.set(x, y, 1, "mangrove_planks" if x not in (25, 35) else lg("spruce_log", "y"))
            d.set(x, b.ridge + 2, 1, sl("cobbled_deepslate"))
            d.set(x, b.yr, 1, "yellow_terracotta")
        b.door(28, 2, "north")
        d.set(28, 2, 1, AIR)
        d.set(28, 3, 1, AIR)
        d.sign(30, b.ridge, 0, "north", ["FREIGHT", "AGENT"], "spruce")
        if L >= 3:
            office = [i for i in wh_list(L, first=False) if i != "ender_chest"]
            furnish(b.room(0, back="south"), "office", office, seats=1)
            furnish(b.room(1, back="south"), "dorm", ["ender_chest"] if L >= 5 else [], beds=1, seats=1)
        else:
            furnish(b.room(0, back="south"), "office", seats=1, sit=False)
    # ---- team stable (L3+) and second depot shed (L4, two storeys at L5)
    if L >= 4:
        e = build(d, 3, 22, 21, 30, 2 if L >= 5 else 1, roof="gable", axis="x", core=(19, 24) if L >= 5 else None)
        e.opening(7, 22, 9, 22, 3, "yellow_terracotta")
        for s_ in range(e.storeys):
            re = e.room(s_, back="north")
            racks += wh_racks(d, re, 4, 25, 16, 29, max(45 if s_ == 0 else 36, WH[L] - racks), "x")
            furnish(re, "loft")
    if L >= 3:
        st_ = build(d, 27, 13, 39, 21, 1, roof="gable", axis="x")
        st_.opening(27, 16, 27, 18, 3, lg("spruce_log", "z"))
        for zz in (14, 17):
            for x in range(35, 39):
                d.set(x, 2, zz, "spruce_fence")
            d.set(38, 2, zz + 1, "hay_block[axis=x]")
        d.set(38, 2, 20, "water_cauldron[level=3]")
        furnish(st_.room(0, back="north"), "loft")                     # harness & feed room
        wagon(d, 29, 25, 2, "spruce", "barrel[facing=up,open=false]")
    if L >= 5:                                                       # teamsters' boarding house + dock crane
        h = build(d, 3, 33, 21, 41, 2, roof="gable", axis="x", core=(19, 35), chimney=(4, 37, "east"))
        h.door(10, 33, "north", double=True)
        furnish(h.room(0, back="south"), "canteen", sit=False)
        furnish(h.room(1, back="south"), "dorm", beds=4)
        for y in range(3, 10):
            d.set(6, y, 3, lg("spruce_log", "y"))
        for z in range(0, 4):
            d.set(6, 10, z, lg("spruce_log", "z"))
        for y in range(6, 10):
            d.set(6, y, 0, CHAIN)
        d.set(6, 5, 0, "hay_block[axis=y]")
        for x in (24, 30, 36, 39):
            lamp_post(d, x, 30, 2, P)
        bench(d, 24, 32, 2, "south", 3, "spruce", sit=False)
        for x, z in ((25, 38), (30, 38), (35, 38), (37, 33)):
            tree(d, x, z, 2, "spruce", 5, 1)
    return d


@design("warehouse")
def warehouse(pack, rel, L):
    return demote({"Neoterra": wh_neo, "Hearthwood": wh_hw, "Cascadia": wh_cas}[pack](rel, L), L)


# =============================================================================================== DELIVERYMAN
"""
Deliveryman
  Neoterra   "Courier depot" (white terracotta panels, orange bands): glass-fronted parcel shop with a counter and
             a wall of parcel barrels (sorting floor upstairs from L2), loading canopy; parcel hub hall with a
             conveyor (L3, crew floor with bunks from L4); van garage with a roof-top drone pad (L5).
  Hearthwood "Post house & coaching stables" (calcite & brick, rose granite roofs, teal shutters): post office
             with a pigeonhole barrel wall, counter and pillar box (sorting loft from L2); coaching stables (L2,
             loft from L3); postmaster's house with the ledgers (L3, guest rooms L4); mail-coach house (L5).
  Cascadia   "Express & freight office" (stripped logs, teal metal roofs, forest-green trim): false-front office
             on a deep porch with a hitching rail (upper floor from L2), stable lean-to (L2); records room annex
             (L3); telegraph & bunk house (L4); freight barn (L5).
"""
DLV = {1: 8, 2: 31, 3: 41, 4: 41, 5: 41}
DSEAT = {1: 0, 2: 3, 3: 6, 4: 6, 5: 6}


def dl_need(L, barrels_done=0):
    """Deliveryman requirements for furnish_all."""
    items = ["crafting_table", "cartography_table"] + (["lectern"] if L >= 2 else []) + \
        (["cartography_table", "lectern"] if L >= 3 else []) + (["ender_chest"] if L >= 5 else [])
    return dict(items=items, barrels=DLV[L] - barrels_done, books=12 if L >= 3 else 0, seats=DSEAT[L],
                beds=1 if L >= 4 else 0)


def dl_neo(rel, L):
    d = Design("Neoterra", rel, (36, 26, 30), paving="smooth_stone")
    P, y0 = "Neoterra", 2
    sto = 1 if L == 1 else 2
    a = build(d, 3, 4, 15, 13, sto, roof="flat", core=(13, 6) if sto > 1 else None, street_glass=True)
    a.door(7, 4, "north", double=True)
    for x in range(3, 16):
        d.set(x, 5, 3, "orange_concrete")
    d.sign(10, 6, 3, "north", ["NEO", "COURIER"], "birch", glow=True, color="orange") if sto > 1 else \
        d.sign(10, 5, 2, "north", ["NEO", "COURIER"], "birch", glow=True, color="orange")
    d.hut(4, y0, 5)
    # parcel shop: sorting wall behind the counter, waiting seats; sorting floor / archive upstairs
    specs = [(a.room(0, back="south"), "sorting")]
    if sto > 1:
        specs.append((a.room(1, back="south"), "library" if L >= 3 else "sorting"))
    b = None
    if L >= 3:
        b = build(d, 18, 4, 32, 14, 3 if L >= 4 else 1, H=4, roof="flat", core=(30, 6) if L >= 4 else None)
        b.opening(22, 4, 24, 4, 3, "orange_concrete")
        for x in range(20, 29):                                      # parcel conveyor
            d.set(x, y0, 9, sl("smooth_stone", "top") if x % 3 else "hopper[enabled=true,facing=down]")
        specs.append((b.room(0, back="south"), "sorting"))
        if L >= 4:
            specs += [(b.room(1, back="south"), "dorm"), (b.room(2, back="south"), "lounge")]
    specs.append((a.room(0, back="north"), "office"))                # waiting seats by the window
    furnish_all(specs, **dl_need(L))
    neo_roof(d, a, [(5, 11, 6, SOLAR), (5, 11, 9, SOLAR), (5, 11, 11, SOLAR)])
    if b:
        neo_roof(d, b, [(20, 22, 6, "iron_block", tr("iron", "north", "bottom"))] + [(20, 28, 9, SOLAR), (20, 28, 12, SOLAR)])
    # forecourt
    for x in (1, 17):
        d.set(x, y0, 3, "moss_block")
        tree(d, x, 3, y0 + 1, "birch", 3, 1)
    lamp_post(d, 12, 1, y0, P)
    if L >= 2:
        for x in range(3, 16):                                       # loading canopy at the back
            for z in range(15, 19):
                d.set(x, 5, z, sl("smooth_quartz", "top"))
        for x in (3, 9, 15):
            d.fill(x, y0, 18, x, 4, 18, "light_gray_concrete")
        a_back = d.door(9, y0, 13, "south", "birch")
        for x in (5, 6, 11, 12):
            crate_stack(d, x, 16, y0, 2)
        bench(d, 4, 1, y0, "north", 2, "birch", sit=False)
    # ---- van garage + drone pad (L5)
    if L >= 5:
        g = build(d, 18, 17, 32, 27, 3, roof="flat", core=(30, 19))
        g.opening(21, 17, 25, 17, 3, "orange_concrete")
        for x in (21, 25):                                           # parked delivery vans
            for z in range(20, 25):
                d.set(x, y0, z, "white_concrete" if z % 2 else "orange_concrete")
                d.set(x, y0 + 1, z, "glass" if z in (21, 22, 23) else sl("smooth_quartz"))
        furnish(g.room(0, back="north"), "workshop")
        furnish(g.room(1, back="south"), "canteen", sit=False)
        furnish(g.room(2, back="south"), "office", seats=3, sit=False)
        yy = g.yr + 1
        for x in range(21, 30):
            for z in range(19, 26):
                d.set(x, yy, z, "orange_concrete" if x in (21, 29) or z in (19, 25) else "light_gray_concrete")
        for x, z in ((23, 21), (27, 21), (23, 23), (27, 23)):
            d.set(x, yy + 1, z, "end_rod[facing=up]")
    return d


def dl_hw(rel, L):
    d = Design("Hearthwood", rel, (36, 22, 40), paving="gravel")
    P, y0 = "Hearthwood", 2
    sto = 1 if L == 1 else 2
    a = build(d, 3, 4, 15, 11, sto, roof="gable", axis="x", core=(13, 5) if sto > 1 else None,
              chimney=(4, 8, "east"))
    a.door(8, 4, "north")
    d.sign(9, 4, 3, "north", ["Royal Mail", "Post House"], "dark_oak")
    d.set(6, y0, 2, "red_concrete")                                     # pillar box
    d.set(6, y0 + 1, 2, "red_terracotta")
    d.set(6, y0 + 2, 2, sl("red_nether_brick"))
    d.hut(5, y0, 5)
    specs = [(a.room(0, back="south"), "sorting")]                    # pigeonholes behind the counter
    if sto > 1:
        specs.append((a.room(1, back="south"), "sorting"))
    flower_bed(d, 10, 2, 14, 2, y0, seed=3)
    lamp_post(d, 2, 2, y0, P)
    if L >= 5:
        spot_trees(d, [(1, 26), (1, 14), (17, 38)], "oak", 4)
    # ---- coaching stables (L2+), loft from L3
    if L >= 2:
        s_ = 2 if L >= 3 else 1
        d.sty_over = dict(wall="bricks", wall0="bricks", end="bricks")
        st_ = build(d, 20, 4, 30, 14, s_, roof="gable", axis="z", core=(28, 8) if s_ > 1 else None)
        d.sty_over = {}
        st_.opening(20, 6, 20, 8, 3, lg("stripped_dark_oak_log", "z"))
        for zz in (6, 9, 12):
            for x in range(22, 26):
                d.set(x, y0, zz, "dark_oak_fence")
            d.set(21, y0, zz + 1, "hay_block[axis=x]") if zz < 12 else None
        rs = st_.room(0, back="east")
        rs.keep |= {(x, z) for x in range(21, 26) for z in range(5, 14)}
        specs.append((rs, "sorting"))                                 # tack & feed barrels
        if s_ > 1:
            specs.append((st_.room(1, back="east"), "loft"))
    # ---- postmaster's house (L3+), guest rooms (L4)
    if L >= 3:
        h = build(d, 3, 15, 15, 23, 2 if L == 3 else 3, roof="gable", axis="x", core=(13, 16), chimney=(4, 19, "east"))
        h.door(8, 15, "north")
        specs += [(h.room(0, back="south"), "library"), (h.room(1, back="south"), "office")]
        if h.storeys > 2:
            specs.append((h.room(2, back="south"), "dorm"))
    specs.append((a.room(0, back="north"), "office"))
    need = dl_need(L)
    if L >= 2:                                                       # customers' bench under the window
        bench(d, 11, 2, y0, "north", 3, "dark_oak")
        need["seats"] -= 3
    furnish_all(specs, **need)
    if L >= 2:
        d.set(17, y0, 7, "stone_bricks")                              # mounting block & trough
        d.set(17, y0, 8, st("stone_brick", "north"))
        for x in (17,):
            d.set(x, y0, 11, "water_cauldron[level=3]")
    # ---- mail-coach house (L4+), sorting office (L5)
    if L >= 5:
        so = build(d, 3, 28, 19, 37, 3, roof="gable", axis="x", core=(17, 30), chimney=(4, 32, "east"))
        so.door(10, 28, "north", double=True)
        for x in range(7, 14):                                       # sorting benches
            d.set(x, so.stand(0), 33, sl("dark_oak", "top"))
            d.chair(x, so.stand(0), 32, "north", "dark_oak", sit=False)
        furnish(so.room(0, back="south"), "sorting", barrels=9)
        furnish(so.room(1, back="south"), "lounge", seats=3, sit=False)
        furnish(so.room(2, back="south"), "dorm", beds=3)
        for x in range(21, 34, 4):
            tree(d, x, 32, y0, "oak", 4, 1)
            tree(d, x + 2, 36, y0, "oak", 4, 1)
        for x in (20, 26, 32):
            lamp_post(d, x, 29, y0, P)
        bench(d, 22, 29, y0, "south", 3, "dark_oak", sit=False)
        d.sign(12, 5, 27, "north", ["Sorting", "Office"], "dark_oak")
    if L >= 4:
        hedge(d, [(34, z) for z in range(2, 38)], y0, "oak")
        for x in (18, 32):
            lamp_post(d, x, 16, y0, P)
        bench(d, 22, 16, y0, "south", 3, "dark_oak", sit=False)
        flower_bed(d, 26, 16, 30, 16, y0, seed=4)
        c = build(d, 20, 18, 33, 26, 2, roof="gable", axis="x", core=(31, 19))
        c.opening(23, 18, 26, 18, 3, lg("stripped_dark_oak_log", "x"))
        wagon(d, 24, 22, y0, "dark_oak", "barrel[facing=up,open=false]")   # the mail coach
        furnish(c.room(0, back="south"), "loft")
        furnish(c.room(1, back="south"), "dorm", beds=2)              # coachmen's rooms
        hedge(d, [(x, 27) for x in range(21, 34)], y0, "oak") if L >= 5 else None
    return d


def dl_cas(rel, L):
    d = Design("Cascadia", rel, (36, 22, 36), paving="coarse_dirt")
    P, y0 = "Cascadia", 2
    sto = 1 if L == 1 else 2
    a = build(d, 3, 7, 13, 14, sto, roof="gable", axis="z", core=(11, 9) if sto > 1 else None)
    mid = 8
    for x in range(2, 15):                                            # false front
        for y in range(a.yr, a.ridge + 2):
            d.set(x, y, 6, "spruce_planks" if x not in (2, 14) else lg("spruce_log", "y"))
        d.set(x, a.ridge + 2, 6, sl("spruce"))
        d.set(x, a.yr, 6, "green_terracotta")
    a.door(mid, 7, "north")
    d.sign(mid, a.ridge, 5, "north", ["EXPRESS", "& FREIGHT"], "spruce")
    # porch with hitching rail
    for x in range(2, 15):
        for z in range(3, 7):
            d.set(x, 1, z, "spruce_planks")
            d.set(x, 6 if sto == 1 else 6, z, sl("warped") if z < 6 else AIR) if z < 6 else None
    for x in (2, 6, 10, 14):
        d.fill(x, y0, 3, x, 5, 3, lg("spruce_log", "y"))
    for x in range(3, 14):
        if abs(x - mid) > 1 and x not in (6, 10):
            d.set(x, y0, 1, "spruce_fence")
    d.hut(4, y0, 8)
    specs = [(a.room(0, back="south"), "sorting")]                    # freight counter & barrel wall
    if sto > 1:
        specs.append((a.room(1, back="south"), "sorting"))
    lamp_post(d, 1, 2, y0, P)
    barrels = 0
    for x in (12, 13):                                                # freight barrels on the porch
        for k in range(2):
            d.item(x, y0 + k, 4, "barrel", "up")
            barrels += 1
    # ---- stable lean-to (L2+)
    if L >= 2:
        for z in range(7, 16):
            for x in range(14, 21):
                d.set(x, 1, z, "spruce_planks")
                d.set(x, 5, z, sl("warped", "top" if x < 16 else "bottom"))
            d.set(20, y0, z, lg("stripped_spruce_log", "z"))
            d.set(20, y0 + 1, z, lg("stripped_spruce_log", "z"))
        for z in (7, 15):
            d.fill(20, y0, z, 20, 4, z, lg("spruce_log", "y"))
        for zz in (9, 12):
            for x in range(17, 20):
                d.set(x, y0, zz, "spruce_fence")
            d.set(19, y0, zz + 1, "hay_block[axis=x]")
        d.set(19, y0, 8, "water_cauldron[level=3]")
        barrels += rack_line(d, [], y0, 0)
        for z in range(10, 15, 1):
            if z in (10, 11, 13, 14):
                for k in range(3):
                    if barrels < DLV[L]:
                        d.item(15, y0 + k, z, "barrel", "east")
                        barrels += 1
    # ---- records room annex (L3+)
    if L >= 3:
        rr = build(d, 3, 16, 13, 23, 2, roof="gable", axis="x", core=(11, 17),
                   chimney=(4, 20, "east"))
        rr.door(8, 16, "north")
        d.set(8, y0, 15, AIR)
        specs += [(rr.room(0, back="south"), "library"), (rr.room(1, back="south"), "office")]
    # ---- telegraph & bunk house (L4+)
    if L >= 4:
        t = build(d, 23, 4, 33, 12, 2, roof="gable", axis="x", core=(31, 5), chimney=(24, 8, "east"))
        t.door(28, 4, "north")
        specs += [(t.room(0, back="south"), "office"), (t.room(1, back="south"), "dorm")]
        for x, z in ring(22, 15, 34, 18):                               # corral
            if d.air(x, y0, z) and x != 22:
                d.set(x, y0, z, "spruce_fence")
        d.set(28, y0, 17, "water_cauldron[level=3]")
        d.set(30, y0, 16, "hay_block[axis=x]")
        for z in (20, 26):
            tree(d, 34, z, y0, "spruce", 5, 1) if L < 5 else None
        for x in (21, 27, 33):
            lamp_post(d, x, 2, y0, P)
        for y in range(y0, t.ridge + 4):                              # telegraph pole
            d.set(34, y, 2, lg("spruce_log", "y") if y < t.ridge + 3 else "spruce_fence")
        d.set(34, t.ridge + 2, 1, "spruce_fence")
        d.set(34, t.ridge + 2, 3, "spruce_fence")
    specs.append((a.room(0, back="north"), "office"))
    need = dl_need(L, barrels)
    if L >= 2:                                                       # waiting bench on the porch
        bench(d, 3, 5, y0, "north", 3, "spruce")
        need["seats"] -= 3
    furnish_all(specs, **need)
    if L >= 4:
        spot_trees(d, [(1, 20), (1, 34), (14, 34)], "spruce", 5)
    # ---- freight barn (L5)
    if L >= 5:
        f = build(d, 16, 19, 33, 33, 2, roof="gable", axis="z", core=(31, 21))
        f.opening(22, 19, 25, 19, 3, lg("spruce_log", "x"))
        wagon(d, 22, 26, y0, "spruce", "hay_block[axis=x]")
        furnish(f.room(0, back="south"), "loft")
        furnish(f.room(1, back="south"), "loft")
    tree(d, 1, 30, y0, "spruce", 5, 2)
    return d


@design("deliveryman")
def deliveryman(pack, rel, L):
    return demote({"Neoterra": dl_neo, "Hearthwood": dl_hw, "Cascadia": dl_cas}[pack](rel, L), L)


# =============================================================================================== COMPOSTER
"""
Composter
  Neoterra   "Green recycling station" (cherry-wood cladding, white fins, lime bands, green roofs): pavilion with
             concrete compost bays in front; sorting shed (L2); glasshouse (L3); two-storey eco learning centre
             (L4); biogas digester domes with a gas holder (L5).
  Hearthwood "Compost yard & potting shed" (mud-brick walls, oak framing, dark shingle roofs): potting shed and
             plank compost bins in a brick-walled garden (enlarged L2); lean-to glasshouse (L3); head gardener's
             cottage (L4); orchard with a barn for leaf-mould and manure (L5).
  Cascadia   "Compost shed" (river-rock walls, dark shake roofs, forest-green trim): pole shed with log-crib bins
             and a mossy roof (longer at L2); mushroom & root house (L3); worm barn (L4, two storeys at L5) and a
             greenhouse (L5).
"""
CBAR = {1: 1, 2: 2, 3: 3, 4: 4, 5: 4}


def bin_bay(d, x, z, y, wall, inner="podzol[snowy=false]", barrel=True, facing="south"):
    """Three-sided compost bay (opening to the south) with a compost barrel or heap inside."""
    for dz in range(3):
        d.set(x, y, z + dz, wall)
        d.set(x + 2, y, z + dz, wall)
    d.set(x + 1, y, z, wall)
    d.set(x + 1, y - 1, z + 2, inner)
    if barrel:
        d.item(x + 1, y, z + 1, "minecolonies:barrel_block", facing)
    else:
        d.set(x + 1, y, z + 1, "composter[level=6]")


def cp_neo(rel, L):
    d = Design("Neoterra", rel, (32, 16, 30), paving="smooth_stone")
    P, y0 = "Neoterra", 2
    a = build(d, 3, 9, 13, 15, 1, roof="flat")
    a.door(8, 9, "north")
    d.sign(6, 4, 8, "north", ["RECYCLE", "& COMPOST"], "cherry", glow=True, color="lime")
    d.hut(4, y0, 10)
    furnish(a.room(0, back="south"), "workshop", ["composter"], racks=min(L, 3), wood="cherry")   # potting room
    neo_roof(d, a, [(5, 11, 11, MOSS), (5, 11, 12, 'azalea'), (5, 11, 13, MOSS)])
    for i in range(min(CBAR[L], 2)):
        bin_bay(d, 3 + i * 4, 4, y0, "light_gray_concrete")
    for x in (1, 15):
        for z in range(9, 16):
            d.set(x, 1, z, "moss_block")
            d.set(x, y0, z, "fern" if z % 2 else "azalea")
    lamp_post(d, 2, 2, y0, P)
    # ---- sorting shed (L2+)
    if L >= 2:
        s_ = build(d, 17, 9, 25, 15, 1, roof="flat")
        s_.opening(20, 9, 22, 9, 3, "lime_concrete")
        rs = s_.room(0, back="south")
        for x in (20, 22):                                            # sorting hoppers
            d.set(x, y0, 12, "hopper[enabled=true,facing=down]")
        d.set(21, y0, 12, sl("smooth_quartz", "top"))
        furnish(rs, "store", racks=L - 3 if L > 3 else 0)
        neo_roof(d, s_, [(19, 23, 11, SOLAR), (19, 23, 13, SOLAR)])
        for i in range(CBAR[L] - 2):
            bin_bay(d, 17 + i * 4, 4, y0, "light_gray_concrete")
    # ---- glasshouse (L3+)
    if L >= 3:
        gx1, gz1, gx2, gz2 = 3, 18, 13, 26
        d.box(gx1, y0, gz1, gx2, 5, gz2, "glass", floor="smooth_stone")
        d.fill(gx1, 6, gz1, gx2, 6, gz2, "glass")
        for x, z in ring(gx1, gz1, gx2, gz2):
            if (x - gx1) % 5 == 0 and z in (gz1, gz2) or x in (gx1, gx2) and (z - gz1) % 4 == 0:
                d.fill(x, y0, z, x, 6, z, "white_concrete")
        d.door(8, y0, gz1, "north", "cherry")
        for x in range(gx1 + 1, gx2):
            for z in (gz1 + 2, gz1 + 3, gz2 - 2, gz2 - 1):
                d.set(x, 1, z, "farmland[moisture=7]")
                d.set(x, y0, z, ["wheat[age=5]", "carrots[age=4]", "potatoes[age=6]", "beetroots[age=2]"][(x + z) % 4])
        for x in (5, 11):
            d.set(x, 5, 22, "end_rod[facing=down]")
    # ---- eco learning centre (L4+)
    if L >= 4:
        e = build(d, 17, 18, 27, 26, 2 if L == 4 else 3, roof="flat", core=(25, 19), street_glass=True)
        e.door(20, 18, "north", double=True)
        furnish(e.room(0, back="south"), "lounge", seats=4, sit=False, wood="cherry")     # visitor foyer
        furnish(e.room(1, back="west"), "library", books=6, seats=2, sit=False, wood="cherry")  # classroom
        if L >= 5:
            furnish(e.room(2, back="south"), "office", seats=2, sit=False, wood="cherry")
        neo_roof(d, e, [(19, 25, 20, MOSS), (19, 25, 21, 'azalea'), (19, 25, 23, MOSS), (19, 25, 24, 'azalea')])
    # ---- biogas digesters (L5)
    if L >= 5:
        for cx, cz in ((29, 6), (29, 13), (29, 20) if False else (22, 6)) if False else ((29, 6), (29, 13)):
            for y in range(y0, 9):
                rr = 2 if y < 6 else 1 if y < 8 else 0
                for dx in range(-2, 3):
                    for dz in range(-2, 3):
                        dist = (dx * dx + dz * dz) ** 0.5
                        if rr - 0.5 <= dist < rr + 0.6 or (rr == 0 and dist < 0.5):
                            d.set(cx + dx, y, cz + dz, "white_concrete" if y % 3 else "lime_concrete")
            d.set(cx, 9, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        for z in range(6, 14):
            d.set(26, y0, z, "light_gray_concrete")
            d.set(26, y0 + 1, z, "iron_bars")
        for x in (27, 31):
            d.fill(x, y0, 22, x, 7, 22, "light_gray_concrete")
            d.fill(x, y0, 26, x, 7, 26, "light_gray_concrete")
        for x in range(27, 32):                                       # gas holder
            for z in range(22, 27):
                if x in (27, 31) or z in (22, 26):
                    d.set(x, 4, z, "iron_bars")
                d.set(x, 8, z, "cut_copper")
        d.set(29, 9, 24, "cut_copper_slab[type=bottom,waterlogged=false]")
        for x in (17, 23):
            lamp_post(d, x, 28, y0, P)
        # drop-off canopy with sorted recycling bins
        for x in range(17, 26):
            d.set(x, 5, 1, sl("smooth_quartz", "top"))
            d.set(x, 5, 2, sl("smooth_quartz", "top"))
        for x in (17, 25):
            d.fill(x, y0, 1, x, 4, 1, "white_concrete")
        for i, c in enumerate(("lime", "cyan", "orange", "yellow", "gray")):
            x = 18 + i
            d.set(x, y0, 1, f"{c}_concrete")
            d.set(x, y0 + 1, 1, f"{c}_carpet")
        # solar carport for the collection vans
        for x in (3, 8, 13):
            for z in (28, 29):
                pass
        for x, z in ((2, 27), (14, 27), (2, 29), (14, 29)):
            d.fill(x, y0, z, x, 4, z, "light_gray_concrete")
        for x in range(1, 16):
            for z in range(27, 30):
                d.set(x, 5, z, "smooth_quartz")
                d.set(x, 6, z, "daylight_detector[inverted=false,power=0]")
        for x in (5, 11):
            d.set(x, y0, 28, "orange_concrete")
            d.set(x + 1, y0, 28, "orange_concrete")
            d.set(x, y0 + 1, 28, "glass")
            d.set(x + 1, y0 + 1, 28, "white_concrete")
        for z in range(18, 27, 4):
            d.set(15, y0, z, "moss_block")
            tree(d, 15, z, y0 + 1, "birch", 3, 1)
        for x in (0, 31):
            for z in (3, 17):
                d.set(x, y0, z, "moss_block")
                tree(d, x, z, y0 + 1, "birch", 3, 1)
        for x in (19, 21, 26):
            lamp_post(d, x, 0, y0, P)
    return d


def cp_hw(rel, L):
    d = Design("Hearthwood", rel, (34, 18, 34), paving="gravel")
    P, y0 = "Hearthwood", 2
    wx2, wz2 = (16, 15) if L == 1 else (24, 19)
    for x, z in ring(2, 3, wx2, wz2):
        d.set(x, y0, z, "bricks")
        d.set(x, y0 + 1, z, "bricks" if z != 3 else "brick_wall")
    for x in (8, 9, 10):
        d.set(x, y0, 3, AIR)
        d.set(x, y0 + 1, 3, AIR)
    for x in (7, 11):
        d.set(x, y0 + 2, 3, LANT_S)
    d.fill(3, 1, 4, wx2 - 1, 1, wz2 - 1, "coarse_dirt")
    a = build(d, 3, 10, 10, 14, 1, roof="gable", axis="x")
    a.door(6, 10, "north")
    d.hut(4, y0, 11)
    furnish(a.room(0, back="south"), "store", ["composter"], racks=min(L, 3), wood="oak")   # potting shed shelves
    for i in range(CBAR[L]):
        bx = 11 + (i % 2) * 4
        bz = 5 + (i // 2) * 5
        bin_bay(d, bx, bz, y0, "spruce_planks")
    for x in range(3, 8):
        for z in (5, 6):
            d.set(x, 1, z, "farmland[moisture=7]")
            d.set(x, y0, z, "carrots[age=5]" if x % 2 else "beetroots[age=2]")
    flower_bed(d, 3, 8, 7, 8, y0, seed=1)
    if L >= 2:
        for x in range(18, 24):
            for z in (5, 6, 8, 9):
                d.set(x, 1, z, "farmland[moisture=7]")
                d.set(x, y0, z, "potatoes[age=7]" if z < 7 else "wheat[age=7]")
        d.set(20, y0, 12, "water_cauldron[level=3]")
        wagon(d, 18, 15, y0, "oak", "podzol[snowy=false]")
        tree(d, 22, 15, y0, "oak", 3, 1)
        tree(d, 13, 17, y0, "oak", 3, 1)
        bench(d, 4, 2, y0, "north", 2, "oak", sit=False)
        for x in (1, 25, 33):
            lamp_post(d, x, 2, y0, P)
        flower_bed(d, 12, 1, 16, 2, y0, seed=3)
    # ---- lean-to glasshouse (L3+)
    if L >= 3:
        for x in range(3, 10):
            for z in (16, 17, 18):
                d.set(x, 1, z, "farmland[moisture=7]" if z > 16 else "gravel")
                if z > 16:
                    d.set(x, y0, z, "melon_stem[age=7]" if x % 2 else "pumpkin_stem[age=7]")
            d.set(x, 5, 15, "glass")
            d.set(x, 4, 16, "glass")
            d.set(x, 3, 17, "glass") if False else None
        for z in (16, 17, 18):
            d.set(3, y0, z, "bricks")
            d.set(9, y0, z, "bricks")
    if L >= 5:
        lamp_post(d, 1, 33, y0, P) if False else lamp_post(d, 30, 30, y0, P)
    # ---- head gardener's cottage (L3, upper floor from L4)
    if L >= 3:
        c = build(d, 3, 22, 13, 29, 2 if L >= 4 else 1, roof="gable", axis="x", core=(11, 23) if L >= 4 else None,
                  chimney=(4, 26, "east"))
        c.door(8, 22, "north")
        d.set(8, y0, 21, AIR) if False else None
        for x in (8,):
            d.set(x, y0, wz2, AIR)
            d.set(x, y0 + 1, wz2, AIR)
        furnish(c.room(0, back="west"), "lounge", racks=max(0, L - 3), wood="oak")   # parlour by the fire
        if L >= 4:
            furnish(c.room(1, back="south"), "dorm", beds=1, wood="oak")
    # ---- leaf-mould barn (L4, loft L5) and orchard (L5)
    if L >= 5:
        bo = build(d, 27, 21, 33, 28, 1, roof="gable", axis="z", chimney=(32, 25, "west"))
        bo.door(27, 24, "west")
        furnish(bo.room(0, back="east"), "dorm", beds=1, wood="oak")    # gardeners' bothy
        for x in (18, 22, 24):
            d.set(x, y0, 31, "beehive[facing=north,honey_level=0]")
        lamp_post(d, 25, 21, y0, P)
        lamp_post(d, 14, 21, y0, P)
        for x in (16, 20, 24) if False else (16, 20):
            for z in (22, 26, 30):
                tree(d, x, z, y0, "oak", 3, 1)
                d.set(x + 1, y0 + 4, z, "flowering_azalea_leaves[distance=1,persistent=true,waterlogged=false]") \
                    if d.air(x + 1, y0 + 4, z) else None
    if L >= 4:
        b = build(d, 26, 3, 33, 18, 2 if L >= 5 else 1, roof="gable", axis="z", core=(31, 5) if L >= 5 else None)
        b.opening(26, 9, 26, 11, 3, lg("stripped_oak_log", "z"))
        furnish(b.room(0, back="east"), "loft")
        if L >= 5:
            furnish(b.room(1, back="east"), "loft")
            hedge(d, [(x, 32) for x in range(0, 34)], y0, "oak")
            hedge(d, [(0, z) for z in range(4, 32)], y0, "oak")
    return d


def cp_cas(rel, L):
    d = Design("Cascadia", rel, (32, 16, 32), paving="coarse_dirt")
    P, y0 = "Cascadia", 2
    x1, z1, z2 = 3, 4, 10
    x2 = 9 if L == 1 else 15
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            d.set(x, 1, z, "packed_mud")
    for x in list(range(x1, x2 + 1, 3)) + [x2]:
        for z in (z1, z2):
            d.fill(x, y0, z, x, 4, z, lg("spruce_log", "y"))
            d.set(x, 1, z, "cobblestone")
    for x in range(x1, x2 + 1):
        d.set(x, 5, z1, lg("stripped_spruce_log", "x"))
        d.set(x, 5, z2, lg("stripped_spruce_log", "x"))
        if d.air(x, y0, z2):
            d.set(x, y0, z2, "mossy_cobblestone")
            d.set(x, y0 + 1, z2, "cobblestone")
    d.gable(x1, z1, x2, z2, 6, "x", "dark_oak_stairs", "dark_oak_slab", "spruce_planks")
    for x in range(x1, x2 + 1):
        for k, z in enumerate(range(z1 - 1, (z1 + z2) // 2)):
            y = 6 + k
            if (x + k) % 3 == 0 and d.air(x, y, z):
                d.set(x, y, z, "moss_carpet")
    d.hut(x1 + 1, y0, z1 + 1)
    d.item(x1 + 1, y0, z2 - 1, "composter")
    rack_line(d, [(x1 + 2, z2 - 1)] + [(x, z2 - 1) for x in range(x1 + 4, x2, 3)], y0, min(L, 2), 1)
    for i in range(CBAR[L]):
        bx = x1 + 2 + i * 3
        d.item(bx, y0, z2 - 2, "minecolonies:barrel_block", "north")
        if d.air(bx - 1, y0, z2 - 2):
            d.set(bx - 1, y0, z2 - 2, lg("spruce_log", "z"))
    d.set(x1 + 3, 4, (z1 + z2) // 2, LANT)
    d.set(x2 + 2, y0, 6, "composter[level=4]")
    for z in range(2, 13):
        d.set(1, y0, z, "spruce_fence")
    lamp_post(d, x1, 2, y0, P)
    if L >= 2:
        for x in range(1, 18):
            d.set(x, y0, 13, "spruce_fence") if x != 8 else None
        wagon(d, x2 + 2, 8, y0, "spruce", "podzol[snowy=false]", "x") if False else None
        tree(d, 18, 3, y0, "spruce", 5, 1)
    # ---- mushroom & root house (L3+)
    if L >= 3:
        m = build(d, 3, 16, 11, 22, 1, roof="gable", axis="x")
        m.door(7, 16, "north")
        for x, z in ((5, 19), (6, 19), (8, 19), (9, 19)):            # mushroom beds
            d.set(x, y0, z, "podzol[snowy=false]")
            d.set(x, y0 + 1, z, "brown_mushroom" if (x + z) % 2 else "red_mushroom")
        furnish(m.room(0, back="south"), "store", racks=L - 2)
        d.set(7, y0, 15, AIR)
    # ---- worm barn (L4, two storeys at L5), greenhouse (L5)
    if L >= 4:
        w = build(d, 18, 6, 28, 16, 2 if L >= 5 else 1, roof="gable", axis="z", core=(26, 8) if L >= 5 else None)
        w.door(22, 6, "north", double=True)
        for z in range(9, 14):                                        # worm beds down the middle
            d.set(23, y0, z, "podzol[snowy=false]" if z % 2 else "rooted_dirt")
        furnish(w.room(0, back="east"), "loft")
        if L >= 5:
            furnish(w.room(1, back="east"), "loft")
    if L >= 5:
        gx1, gz1, gx2, gz2 = 15, 19, 27, 27
        d.box(gx1, y0, gz1, gx2, 4, gz2, "glass", floor="spruce_planks")
        for x, z in ring(gx1, gz1, gx2, gz2):
            if (x - gx1) % 4 == 0 or (z - gz1) % 4 == 0:
                d.fill(x, y0, z, x, 4, z, lg("spruce_log", "y"))
        d.gable(gx1, gz1, gx2, gz2, 5, "x", "glass_pane" if False else "spruce_stairs", "spruce_slab", "glass")
        d.door(21, y0, gz1, "north", "spruce")
        for x in range(gx1 + 1, gx2):
            for z in (gz1 + 2, gz2 - 2):
                d.set(x, 1, z, "farmland[moisture=7]")
                d.set(x, y0, z, "carrots[age=5]" if x % 2 else "potatoes[age=6]")
        tree(d, 30, 29, y0, "spruce", 5, 1)
    return d


@design("composter")
def composter(pack, rel, L):
    return demote({"Neoterra": cp_neo, "Hearthwood": cp_hw, "Cascadia": cp_cas}[pack](rel, L), L)
