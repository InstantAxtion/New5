"""
Military & mystic orders: guardtower, archery, combatacademy, enchanter, alchemist, graveyard, mysticalsite.

Guard tower
  Hearthwood  Village watch tower: square stone-brick ground storey, timber-framed bunk room above, steep hipped
              tile roof; L2 adds an open lookout storey with an alarm bell, L3 an armoury wing, L4 a fenced drill
              yard with dummies, L5 a jettied lookout gallery with banners.
  Cascadia    Fire lookout: log bunk cabin with porch and stone chimney beside a timber trestle tower with a glazed
              cab and catwalk on top; the tower grows taller every level, L3 woodshed, L5 flag and water tank.
  Neoterra    Security tower: glazed guard lobby with crew room and a slim concrete shaft carrying a cantilevered
              glass observation pod with antenna; the shaft grows each level, L3 roof terrace, L4 armoury wing.
Archery, combat academy, enchanter, alchemist, graveyard, mystical site: see the section headers below.
"""
from hm import Design, design, AIR, D4, OPP, CW

ST = lambda m, f, h="bottom", s="straight": f"{m}_stairs[facing={f},half={h},shape={s},waterlogged=false]"
SL = lambda m, t="bottom": f"{m}_slab[type={t},waterlogged=false]"
TD = lambda m, f, h="top", o="false": f"{m}_trapdoor[facing={f},half={h},open={o},powered=false,waterlogged=false]"
LOG = lambda m, a="y": f"{m}[axis={a}]"
LANT = "lantern[hanging=true,waterlogged=false]"
LANT_S = "lantern[hanging=false,waterlogged=false]"
SLANT = "soul_lantern[hanging=true,waterlogged=false]"
ROD = lambda f="up": f"lightning_rod[facing={f},powered=false,waterlogged=false]"
ENDROD = lambda f="up": f"end_rod[facing={f}]"


def soft(d, fn, *a, **k):
    """Run a drawing helper so that it only writes into air cells (roofs meeting existing walls)."""
    orig = d.set

    def s(x, y, z, b, te=None):
        if d.bp.inside(x, y, z) and d.air(x, y, z):
            orig(x, y, z, b, te)
    d.set = s
    try:
        return fn(*a, **k)
    finally:
        del d.set


def ladder(d, x, z, y1, y2, facing):
    """Ladder column (facing away from the supporting wall) from y1 to y2 inclusive (y2 = the deck hole)."""
    for y in range(y1, y2 + 1):
        d.set(x, y, z, f"ladder[facing={facing},waterlogged=false]")


def flight(d, x, y, z, dirn, n, mat, under=None):
    """Straight stair flight rising toward `dirn`; first step at (x,y,z). Clears 3 cells of headroom above
    each step (cuts the hole in the deck above). Returns the cell after the top step."""
    dx, dz = D4[dirn]
    for i in range(n):
        cx, cz = x + dx * i, z + dz * i
        d.set(cx, y + i, cz, ST(mat, dirn))
        if under:
            for yy in range(y, y + i):
                d.set(cx, yy, cz, under)
        for k in range(1, 4):
            if d.bp.inside(cx, y + i + k, cz):
                d.set(cx, y + i + k, cz, AIR)
    return x + dx * n, z + dz * n


def dummy(d, x, y, z, facing="north", head="carved_pumpkin"):
    """Training dummy: fence post, hay-bale body, pumpkin head."""
    d.set(x, y, z, "oak_fence")
    d.set(x, y + 1, z, "hay_block[axis=y]")
    d.set(x, y + 2, z, f"{head}[facing={facing}]")


def weapon_rack(d, x1, z1, x2, z2, y, wood, facing):
    """Wall rack: shelf slab with spears (lightning rods) and shields (banners) above."""
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for z in range(min(z1, z2), max(z1, z2) + 1):
            d.set(x, y, z, SL(wood, "top"))
            d.set(x, y + 1, z, ROD())


def hw_frame(d, x1, z1, x2, z2, y1, y2, step=2, beam="stripped_dark_oak_log", infill="calcite"):
    """Timber-framed storey walls (calcite infill, dark-oak studs every `step`, top beam)."""
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if not (x in (x1, x2) or z in (z1, z2)):
                continue
            for y in range(y1, y2 + 1):
                stud = (x in (x1, x2) and (z - z1) % step == 0) or (z in (z1, z2) and (x - x1) % step == 0) \
                    or (x in (x1, x2) and z in (z1, z2))
                if y == y2:
                    d.set(x, y, z, LOG(beam, "x" if z in (z1, z2) else "z"))
                else:
                    d.set(x, y, z, LOG(beam) if stud else infill)


def cs_walls(d, x1, z1, x2, z2, y1, y2, log="spruce_log", corner="stripped_spruce_log", footing=True):
    """Log-cabin walls: horizontal logs, stripped corner posts, river-rock footing on the ground row."""
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if not (x in (x1, x2) or z in (z1, z2)):
                continue
            corner_ = x in (x1, x2) and z in (z1, z2)
            for y in range(y1, y2 + 1):
                d.set(x, y, z, LOG(corner) if corner_ else LOG(log, "x" if z in (z1, z2) else "z"))
            if footing:
                d.set(x, y1 - 1, z, "mossy_cobblestone" if (x * 7 + z * 3) % 4 == 0 else "cobblestone")
                d.set(x, y1, z, RIVER[(x * 5 + z * 3) % len(RIVER)])


RIVER = ["cobblestone", "mossy_cobblestone", "andesite", "cobblestone", "tuff", "mossy_cobblestone"]


def cs_roof(d, x1, z1, x2, z2, y, axis, end="spruce_planks", o=1, tiles="deepslate_tile"):
    """Cascadia roof: dark deepslate-tile slopes, a stripped-log ridge beam and light spruce barge boards /
    fascia along the gable edges and the eaves. Returns the ridge height."""
    ridge = soft(d, d.gable, x1, z1, x2, z2, y, axis, f"{tiles}_stairs",
                 LOG("stripped_spruce_log", axis), end, o)
    if axis == "x":
        ends = [(x1 - o, z) for z in range(z1 - o, z2 + o + 1)] + [(x2 + o, z) for z in range(z1 - o, z2 + o + 1)]
        eaves = [(x, z1 - o) for x in range(x1 - o, x2 + o + 1)] + [(x, z2 + o) for x in range(x1 - o, x2 + o + 1)]
    else:
        ends = [(x, z1 - o) for x in range(x1 - o, x2 + o + 1)] + [(x, z2 + o) for x in range(x1 - o, x2 + o + 1)]
        eaves = [(x1 - o, z) for z in range(z1 - o, z2 + o + 1)] + [(x2 + o, z) for z in range(z1 - o, z2 + o + 1)]
    for x, z in ends + eaves:
        for yy in range(y - o, ridge + 1):
            if d.bp.inside(x, yy, z) and d.get(x, yy, z).startswith(f"minecraft:{tiles}_stairs"):
                d.set(x, yy, z, d.get(x, yy, z).replace(f"{tiles}_stairs", "spruce_stairs"))
    return ridge


def cs_trim(d, x1, z1, x2, z2, y1, y2):
    """Stripped-log trims on a log building: lintels and sills round windows, jambs beside doors."""
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if not (x in (x1, x2) or z in (z1, z2)):
                continue
            ax = "x" if z in (z1, z2) else "z"
            for y in range(y1, y2 + 1):
                b = d.get(x, y, z)
                if "glass_pane" in b:
                    for yy in (y - 1, y + 1):
                        n = d.get(x, yy, z)
                        if n.startswith("minecraft:spruce_log") or n.startswith("minecraft:dark_oak_log"):
                            d.set(x, yy, z, LOG("stripped_spruce_log", ax))
                if "_door[" in b and "half=lower" in b:
                    for dx, dz in (((1, 0), (-1, 0)) if ax == "x" else ((0, 1), (0, -1))):
                        for yy in (y, y + 1, y + 2):
                            n = d.get(x + dx, yy, z + dz) if d.bp.inside(x + dx, yy, z + dz) else ""
                            if n.startswith("minecraft:spruce_log") or n.split("[")[0] in \
                                    ["minecraft:" + r for r in RIVER]:
                                d.set(x + dx, yy, z + dz, LOG("stripped_spruce_log"))


def nt_walls(d, x1, z1, x2, z2, y1, y2, wall="white_concrete", corner="light_gray_concrete"):
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if not (x in (x1, x2) or z in (z1, z2)):
                continue
            c = x in (x1, x2) and z in (z1, z2)
            for y in range(y1, y2 + 1):
                d.set(x, y, z, corner if c else wall)


def interior(d, x1, z1, x2, z2, y1, y2):
    d.clear(x1 + 1, y1, z1 + 1, x2 - 1, y2, z2 - 1)


def hipcap(d, x1, z1, x2, z2, y, stairs, cap, ceiling, overhang=1):
    """Hip roof with a flat ceiling under it (fills the inner area at y so the attic is closed)."""
    d.fill(x1 + 1, y, z1 + 1, x2 - 1, y, z2 - 1, ceiling)
    return soft(d, d.hip, x1, z1, x2, z2, y, stairs, cap, overhang)


# ================================================================================================ BUILDING KIT
# Grown levels are made of real buildings: building() draws a furnished pack-style building (walls, floors, stair,
# windows with shutters / boxes, doors with canopy lamps, roof with chimney), furnish() fills a room for its use.

FLOWERS = ["potted_red_tulip", "potted_azure_bluet", "potted_oxeye_daisy", "potted_allium", "potted_cornflower",
           "potted_blue_orchid", "potted_poppy", "potted_dandelion"]


def _out(side):
    return D4[side]


def _sides(x1, z1, x2, z2):
    """Yield (side, x, z) for the wall cells (no corners) of a rectangle."""
    for x in range(x1 + 1, x2):
        yield "north", x, z1
        yield "south", x, z2
    for z in range(z1 + 1, z2):
        yield "west", x1, z
        yield "east", x2, z


class Bld:
    pass


def building(d, x1, z1, x2, z2, nf=1, axis="x", roof="gable", doors=(("north", None),), y0=2, ground=None,
             stairs=True, chimney=None, win=3, kinds=None, overhang=1, wood=None, lamps=True, beams=True,
             flat_deco=True, wall=None, ridge_hip=False):
    """Pack-style building on the rectangle x1..x2/z1..z2 (walls included), nf storeys of 5 (walk y, y+5, ...).
    doors: (side, position-along-wall or None for the middle). kinds: room kind per storey for furnish()."""
    P = d.pack
    b = Bld()
    b.x1, b.z1, b.x2, b.z2, b.nf = x1, z1, x2, z2, nf
    b.walks = [y0 + 5 * i for i in range(nf)]
    b.top = y0 + 5 * nf - 1                           # eave level (roof starts here)
    wood = wood or {"Hearthwood": "dark_oak", "Cascadia": "spruce", "Neoterra": "birch"}[P]
    b.wood = wood
    res = set()
    # ---- shell
    for i, y in enumerate(b.walks):
        if P == "Hearthwood":
            if i == 0 and ground != "frame":
                gm = ground or "bricks"
                for s, x, z in list(_sides(x1, z1, x2, z2)) + [("c", x1, z1), ("c", x2, z1), ("c", x1, z2), ("c", x2, z2)]:
                    for yy in range(y, y + 4):
                        corner = s == "c"
                        d.set(x, yy, z, ("stone_bricks" if (yy - y) % 2 == 0 else "polished_andesite")
                              if corner and gm == "bricks" else gm)
                    d.set(x, y, z, "stone_bricks")
                    d.set(x, 1, z, "stone_bricks")
            else:
                hw_frame(d, x1, z1, x2, z2, y, y + 3, 2)
                if i == 0:
                    for s, x, z in list(_sides(x1, z1, x2, z2)) + [("c", x1, z1), ("c", x2, z1), ("c", x1, z2), ("c", x2, z2)]:
                        d.set(x, y, z, "stone_bricks")
                        d.set(x, 1, z, "stone_bricks")
            band = "stripped_dark_oak_log"
        elif P == "Cascadia":
            if i == 0:
                cs_walls(d, x1, z1, x2, z2, y, y + 3)
            else:
                sid = SIDING.get(d.req["base"], "spruce_planks")
                for s, x, z in _sides(x1, z1, x2, z2):
                    for yy in range(y, y + 4):
                        along = x if s in ("north", "south") else z
                        d.set(x, yy, z, LOG("stripped_spruce_log") if along % 2 == 0 else sid)
                for x, z in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
                    for yy in range(y, y + 4):
                        d.set(x, yy, z, LOG("spruce_log"))
            band = "dark_oak_log"
        else:
            nt_walls(d, x1, z1, x2, z2, y, y + 3, wall or "white_concrete", "light_gray_concrete")
            if i == 0:
                for s, x, z in _sides(x1, z1, x2, z2):
                    d.set(x, 1, z, "polished_andesite")
            band = None
        d.clear(x1 + 1, y, z1 + 1, x2 - 1, y + 3, z2 - 1)
        if i == 0:
            d.fill(x1 + 1, y - 1, z1 + 1, x2 - 1, y - 1, z2 - 1,
                   {"Hearthwood": "oak_planks", "Cascadia": "spruce_planks", "Neoterra": "polished_diorite"}[P])
        if i < nf - 1 or roof == "flat":
            deck = {"Hearthwood": "dark_oak_planks", "Cascadia": "spruce_planks", "Neoterra": "light_gray_concrete"}[P]
            d.fill(x1 + 1, y + 4, z1 + 1, x2 - 1, y + 4, z2 - 1, deck)
            for s, x, z in list(_sides(x1, z1, x2, z2)) + [("c", x1, z1), ("c", x2, z1), ("c", x1, z2), ("c", x2, z2)]:
                if band:
                    d.set(x, y + 4, z, LOG(band, "x" if s in ("north", "south") else "z" if s != "c" else "y"))
                else:
                    d.set(x, y + 4, z, "cyan_terracotta" if i < nf - 1 else "white_concrete")
    # ---- windows (none on or right beside a door)
    dcells = set()
    for side, pos in doors:
        if side in ("north", "south"):
            px = pos if pos is not None else (x1 + x2) // 2
            dcells |= {(px + k, z1 if side == "north" else z2) for k in (-1, 0, 1)}
        else:
            pz = pos if pos is not None else (z1 + z2) // 2
            dcells |= {(x1 if side == "west" else x2, pz + k) for k in (-1, 0, 1)}
    for i, y in enumerate(b.walks):
        for s, x, z in _sides(x1, z1, x2, z2):
            if i == 0 and (x, z) in dcells:
                continue
            along = (x - x1) if s in ("north", "south") else (z - z1)
            length = (x2 - x1) if s in ("north", "south") else (z2 - z1)
            if P == "Neoterra":
                if along % 4 == 0:
                    continue
                d.window(x, y + (0 if i else 1), z, x, y + 2, z, "glass_pane" if i == 0 else "light_gray_stained_glass_pane")
                continue
            if along < 2 or length - along < 2 or (along - 2) % win:
                continue
            d.window(x, y + 1, z, x, y + 2, z)
            ox, oz = _out(s)
            o = (x + ox, z + oz)
            if not d.bp.inside(o[0], y + 2, o[1]):
                continue
            if i == 0:
                for k in (-1, 1):                                     # shutters
                    sx, sz = (x + k, z) if s in ("north", "south") else (x, z + k)
                    if d.bp.inside(sx + ox, y + 1, sz + oz) and d.air(sx + ox, y + 1, sz + oz):
                        for yy in (y + 1, y + 2):
                            d.set(sx + ox, yy, sz + oz, TD(wood if P != "Cascadia" else "spruce", s, "bottom", "true"))
            elif d.air(o[0], y, o[1]):
                d.set(o[0], y, o[1], TD(wood, s, "top", "false"))      # window box
                d.set(o[0], y + 1, o[1], FLOWERS[(x * 3 + z + y) % len(FLOWERS)])
    if P == "Cascadia":
        cs_trim(d, x1, z1, x2, z2, b.walks[0], b.top - 1)
    # ---- doors
    b.doors = []
    for side, pos in doors:
        if side in ("north", "south"):
            x = pos if pos is not None else (x1 + x2) // 2
            z = z1 if side == "north" else z2
        else:
            z = pos if pos is not None else (z1 + z2) // 2
            x = x1 if side == "west" else x2
        y = y0
        d.door(x, y, z, OPP[side], wood)
        d.set(x, y + 2, z, {"Hearthwood": LOG("stripped_dark_oak_log", "x" if side in ("north", "south") else "z"),
                            "Cascadia": LOG("stripped_spruce_log", "x" if side in ("north", "south") else "z"),
                            "Neoterra": "light_gray_concrete"}[P])
        ox, oz = _out(side)
        ix, iz = x - ox, z - oz
        res |= {(ix, iz), (ix - ox, iz - oz)}
        b.doors.append((x, z, side))
        if lamps:
            cx, cz = x + ox, z + oz
            for k in (-1, 0, 1):
                px, pz = (cx + k, cz) if side in ("north", "south") else (cx, cz + k)
                if d.bp.inside(px, y + 3, pz) and d.air(px, y + 3, pz):
                    d.set(px, y + 3, pz, SL(wood if P != "Neoterra" else "smooth_quartz", "top") if P != "Cascadia"
                          else SL("spruce", "top"))
            for k in (-1, 1):
                px, pz = (cx + k, cz) if side in ("north", "south") else (cx, cz + k)
                if d.bp.inside(px, y + 2, pz) and d.air(px, y + 2, pz) and d.get(px, y + 3, pz) != AIR:
                    d.set(px, y + 2, pz, LANT if P != "Neoterra" else "end_rod[facing=down]")
            if d.bp.inside(cx, 1, cz):
                d.set(cx, 1, cz, {"Hearthwood": "gravel", "Cascadia": "coarse_dirt", "Neoterra": "smooth_stone"}[P]) \
                    if False else None
    # ---- stairs (switchback along the south wall)
    b.stair = set()
    if nf > 1 and stairs:
        sx = x1 + 1
        for i in range(nf - 1):
            y = b.walks[i]
            if i % 2 == 0:
                flight(d, sx, y, z2 - 1, "east", 4, wood if P != "Neoterra" else "smooth_quartz")
            else:
                flight(d, sx + 4, y, z2 - 2, "west", 4, wood if P != "Neoterra" else "smooth_quartz")
        for x in range(sx, sx + 6):
            for z in (z2 - 1, z2 - 2, z2 - 3):
                b.stair.add((x, z))
        # rail round the top hole
        i = nf - 2
        yt = b.walks[-1]
        row = z2 - 2 if i % 2 == 0 else z2 - 3
        for x in range(sx + 1, sx + 4):
            if d.air(x, yt, row) and d.get(x, yt - 1, row) != AIR:
                d.set(x, yt, row, f"{wood if P != 'Neoterra' else 'birch'}_fence")
    res |= b.stair
    b.res = res
    # ---- roof
    if roof == "flat":
        d.flat(x1, z1, x2, z2, b.top, None, None, None) if False else None
        for s, x, z in list(_sides(x1, z1, x2, z2)) + [("c", x1, z1), ("c", x2, z1), ("c", x1, z2), ("c", x2, z2)]:
            d.set(x, b.top + 1, z, {"Neoterra": "white_concrete", "Hearthwood": "stone_bricks",
                                    "Cascadia": "spruce_planks"}[P])
            d.set(x, b.top + 2, z, SL({"Neoterra": "smooth_quartz", "Hearthwood": "stone_brick",
                                       "Cascadia": "spruce"}[P]))
        if P == "Neoterra":
            d.fill(x1 + 1, b.top, z1 + 1, x2 - 1, b.top, z2 - 1, "smooth_quartz")
        if flat_deco and P == "Neoterra":
            roof_deco(d, x1 + 1, z1 + 1, x2 - 1, z2 - 1, b.top + 1)
        for x in range(x1 + 2, x2 - 1, 4):
            for z in range(z1 + 2, z2 - 1, 4):
                if d.get(x, b.top, z) != AIR and (x, z) not in b.stair:
                    d.set(x, b.top, z, "pearlescent_froglight[axis=y]" if P == "Neoterra" else d.get(x, b.top, z))
        b.ridge = b.top + 2
    elif roof == "hip":
        tiles = {"Hearthwood": "deepslate_tile", "Cascadia": "deepslate_tile", "Neoterra": "smooth_quartz"}[P]
        b.ridge = hipcap(d, x1, z1, x2, z2, b.top, f"{tiles}_stairs", f"{tiles}_slab",
                         {"Hearthwood": "dark_oak_planks", "Cascadia": "spruce_planks", "Neoterra": "white_concrete"}[P])
    else:
        if P == "Cascadia":
            b.ridge = cs_roof(d, x1, z1, x2, z2, b.top, axis)
        else:
            end = "calcite" if P == "Hearthwood" else "white_concrete"
            b.ridge = soft(d, d.gable, x1, z1, x2, z2, b.top, axis, "deepslate_tile_stairs", "deepslate_tile_slab",
                           end, overhang)
            if P == "Hearthwood":                                     # king posts + gable window
                for a in ((x1, x2) if axis == "x" else (z1, z2)):
                    m = (z1 + z2) // 2 if axis == "x" else (x1 + x2) // 2
                    for yy in range(b.top, b.ridge):
                        x, z = (a, m) if axis == "x" else (m, a)
                        if d.get(x, yy, z) == "minecraft:calcite":
                            d.set(x, yy, z, LOG("stripped_dark_oak_log"))
                    for k in (-1, 1):
                        x, z = (a, m + k) if axis == "x" else (m + k, a)
                        if d.get(x, b.top + 1, z) == "minecraft:calcite":
                            d.set(x, b.top + 1, z, "glass_pane")
        if beams and P != "Neoterra":                                 # exposed tie beams under the roof
            yb = b.top
            if axis == "x":
                for x in range(x1 + 2, x2 - 1, 3):
                    for z in range(z1 + 1, z2):
                        if d.air(x, yb, z):
                            d.set(x, yb, z, LOG(f"stripped_{wood}_log" if wood != "birch" else "stripped_birch_log", "z"))
            else:
                for z in range(z1 + 2, z2 - 1, 3):
                    for x in range(x1 + 1, x2):
                        if d.air(x, yb, z):
                            d.set(x, yb, z, LOG(f"stripped_{wood}_log" if wood != "birch" else "stripped_birch_log", "x"))
    # ---- chimney
    if chimney:
        cx, cz = chimney
        mat = {"Hearthwood": "bricks", "Cascadia": "cobblestone", "Neoterra": "light_gray_concrete"}[P]
        for yy in range(1, b.ridge + 2):
            d.set(cx, yy, cz, mat if P != "Cascadia" or yy % 3 else "mossy_cobblestone")
        d.set(cx, b.ridge + 2, cz, {"Hearthwood": "brick_wall", "Cascadia": "cobblestone_wall",
                                    "Neoterra": "iron_bars"}[P])
    # ---- rooms
    if kinds:
        for i, y in enumerate(b.walks):
            k = kinds[i] if i < len(kinds) else kinds[-1]
            if k:
                furnish(d, k, x1 + 1, z1 + 1, x2 - 1, z2 - 1, y, b.res, wood, top=(i == nf - 1 and roof != "flat"))
    return b


SIDING = {"archery": "birch_planks", "combatacademy": "mangrove_planks", "alchemist": "cherry_planks",
          "graveyard": "birch_planks", "enchanter": "dark_oak_planks", "guardtower": "spruce_planks"}

# Per type palette inside each pack (block renames applied to the finished building): roof tiles, wall washes,
# timber, shutter / door colours and accent bands differ between the types of a pack.
_ROOF = lambda a, b: {"deepslate_tile_stairs": f"{b}_stairs", "deepslate_tile_slab": f"{b}_slab"}
REMAP = {
    ("Hearthwood", "guardtower"): {"dark_oak_trapdoor": "crimson_trapdoor", "dark_oak_door": "crimson_door"},
    ("Hearthwood", "archery"): {**_ROOF(0, "brick"), "calcite": "yellow_terracotta",
                                "stripped_dark_oak_log": "stripped_oak_log", "dark_oak_trapdoor": "warped_trapdoor",
                                "dark_oak_door": "warped_door"},
    ("Hearthwood", "combatacademy"): {**_ROOF(0, "granite"), "calcite": "white_terracotta", "bricks": "mud_bricks",
                                      "dark_oak_trapdoor": "mangrove_trapdoor", "dark_oak_door": "mangrove_door"},
    ("Hearthwood", "enchanter"): {**_ROOF(0, "dark_prismarine"), "calcite": "smooth_sandstone",
                                  "bricks": "sandstone", "dark_oak_trapdoor": "warped_trapdoor",
                                  "stripped_dark_oak_log": "stripped_oak_log", "dark_oak_door": "oak_door"},
    ("Hearthwood", "alchemist"): {**_ROOF(0, "mud_brick"), "calcite": "pink_terracotta",
                                  "dark_oak_trapdoor": "bamboo_trapdoor", "dark_oak_door": "bamboo_door"},
    ("Hearthwood", "graveyard"): {**_ROOF(0, "stone_brick"), "dark_oak_trapdoor": "spruce_trapdoor"},
    ("Hearthwood", "mysticalsite"): {"dark_oak_slab": "spruce_slab"},
    ("Cascadia", "guardtower"): {**_ROOF(0, "dark_prismarine"), "spruce_trapdoor": "mangrove_trapdoor",
                                 "spruce_door": "mangrove_door"},
    ("Cascadia", "archery"): {**_ROOF(0, "mangrove"), "spruce_trapdoor": "dark_oak_trapdoor",
                              "spruce_door": "dark_oak_door"},
    ("Cascadia", "combatacademy"): {**_ROOF(0, "cobbled_deepslate"), "spruce_log": "stripped_mangrove_log",
                                    "stripped_spruce_log": "stripped_birch_log", "spruce_trapdoor": "birch_trapdoor",
                                    "spruce_door": "birch_door"},
    ("Cascadia", "enchanter"): {"spruce_log": "dark_oak_log", "spruce_trapdoor": "bamboo_trapdoor",
                                "spruce_door": "bamboo_door"},
    ("Cascadia", "alchemist"): {**_ROOF(0, "dark_oak"), "spruce_trapdoor": "warped_trapdoor",
                                "spruce_door": "warped_door"},
    ("Cascadia", "graveyard"): {**_ROOF(0, "cobbled_deepslate"), "spruce_trapdoor": "mangrove_trapdoor"},
    ("Cascadia", "mysticalsite"): {**_ROOF(0, "mangrove")},
    ("Neoterra", "guardtower"): {"cyan_terracotta": "orange_terracotta", "white_concrete": "light_gray_concrete",
                                 "light_gray_concrete": "gray_concrete", "cyan_concrete": "orange_concrete"},
    ("Neoterra", "archery"): {"light_gray_concrete": "mangrove_planks"},
    ("Neoterra", "combatacademy"): {"cyan_terracotta": "yellow_terracotta", "cyan_concrete": "yellow_concrete",
                                    "light_gray_concrete": "polished_blackstone", "birch_door": "mangrove_door"},
    ("Neoterra", "enchanter"): {"cyan_terracotta": "magenta_terracotta", "light_gray_concrete": "quartz_bricks"},
    ("Neoterra", "alchemist"): {"cyan_terracotta": "lime_terracotta", "light_gray_concrete": "birch_planks"},
    ("Neoterra", "graveyard"): {"light_gray_concrete": "cherry_planks", "cyan_terracotta": "green_terracotta"},
    ("Neoterra", "mysticalsite"): {"white_concrete": "quartz_bricks"},
}


def repaint(d):
    m = REMAP.get((d.pack, d.req["base"]))
    if not m:
        return d
    m = {"minecraft:" + k: "minecraft:" + v for k, v in m.items()}
    g = d.bp.grid
    for y in range(len(g)):
        for z in range(len(g[y])):
            row = g[y][z]
            for x in range(len(row)):
                st = row[x]
                n, _, rest = st.partition("[")
                if n in m:
                    row[x] = m[n] + ("[" + rest if rest else "")
    return d


def tidy(d):
    """Remove ground-level shutters / window boxes that would block a narrow alley (less than 3 free cells
    outside them) so everything stays walkable."""
    for x in range(d.sx):
        for z in range(d.sz):
            for y in (2, 3, 4):
                s = d.get(x, y, z)
                if "trapdoor" not in s or "iron" in s:
                    continue
                from hm import parse_state  # noqa
                props = dict(kv.split("=") for kv in s.split("[")[1].rstrip("]").split(","))
                f = props["facing"]
                shutter = props["open"] == "true" and y in (3, 4)
                box = props["open"] == "false" and props["half"] == "top" and y == 2
                if not (shutter or box):
                    continue
                ox, oz = D4[f]
                bx, bz = x - ox, z - oz                                 # the wall behind it
                if not d.bp.inside(bx, y, bz) or d.air(bx, y, bz):
                    continue
                ok = not any("door" in d.get(bx, yy, bz) for yy in (2, 3))
                for k in (1, 2):
                    cx, cz = x + ox * k, z + oz * k
                    if not d.bp.inside(cx, 2, cz):
                        ok = False
                        break
                    if not (d.air(cx, 2, cz) and d.air(cx, 3, cz)) and "carpet" not in d.get(cx, 2, cz):
                        ok = False
                if not ok:
                    d.set(x, y, z, AIR)
                    if box and d.get(x, y + 1, z).startswith("minecraft:potted_"):
                        d.set(x, y + 1, z, AIR)
    return repaint(d)


def roof_deco(d, x1, z1, x2, z2, y):
    """Neoterra roof: solar panel rows, an AC unit and planters along the parapet."""
    w = x2 - x1 + 1
    for x in range(x1 + 1, x2, 2):
        for z in range(z1 + 1, z2):
            if (z - z1) % 3 == 0 or not d.air(x, y, z):
                continue
            if x < x1 + max(2, w // 2):
                d.set(x, y, z, "daylight_detector[inverted=false,power=0]")
    if d.air(x2 - 1, y, z1 + 1):
        d.set(x2 - 1, y, z1 + 1, "iron_block")
        d.set(x2 - 1, y + 1, z1 + 1, "iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
    for z in range(z1 + 2, z2, 3):
        if d.air(x2, y, z):
            pass
        if d.air(x2 - 1, y, z):
            d.set(x2 - 1, y, z, "azalea")


# ---------------------------------------------------------------------------------------------- furnish
def _wallside(d, x, z, ix1, iz1, ix2, iz2):
    if z == iz1:
        return "north"
    if z == iz2:
        return "south"
    if x == ix1:
        return "west"
    return "east"


def furnish(d, kind, ix1, iz1, ix2, iz2, y, res, wood, top=False, extra=None):
    """Furnish the room ix1..ix2/iz1..iz2 (inner cells) on walk layer y for `kind`. Items go round the walls
    (ring), the next ring stays an aisle, centre pieces sit in the middle. Cells in `res` stay free."""
    P = d.pack
    w, dp = ix2 - ix1 + 1, iz2 - iz1 + 1

    def free(x, z, h=2):
        return (x, z) not in res and all(d.air(x, y + k, z) for k in range(h)) and d.get(x, y - 1, z) != AIR

    def tall_ok(x, z, side):
        ox, oz = D4[side]
        return "glass" not in d.get(x + ox, y + 1, z + oz) and "door" not in d.get(x + ox, y, z + oz)

    ring = []
    for x in range(ix1, ix2 + 1):
        ring.append((x, iz1))
    for z in range(iz1 + 1, iz2 + 1):
        ring.append((ix2, z))
    for x in range(ix2 - 1, ix1 - 1, -1):
        ring.append((x, iz2))
    for z in range(iz2 - 1, iz1, -1):
        ring.append((ix1, z))
    corners = {(ix1, iz1), (ix2, iz1), (ix1, iz2), (ix2, iz2)}
    lamp = LANT if P != "Neoterra" else "sea_lantern"
    seq = KINDS.get(kind, KINDS["store"])(d, wood)
    n = 0
    for (x, z) in ring:
        side = _wallside(d, x, z, ix1, iz1, ix2, iz2)
        if (x, z) in corners:
            if free(x, z):
                d.set(x, y, z, seq["corner"] if "corner" in seq else FLOWERS[(x + z) % 8].replace("potted_", "potted_") if False
                      else seq.get("corner", "potted_fern" if P != "Neoterra" else "potted_bamboo"))
            continue
        if not free(x, z):
            continue
        item = seq["ring"][n % len(seq["ring"])]
        n += 1
        if item is None:
            continue
        item(d, x, y, z, OPP[side], tall_ok(x, z, side))
    # centre
    cx1, cz1, cx2, cz2 = ix1 + 2, iz1 + 2, ix2 - 2, iz2 - 2
    if "centre" in seq and cx2 >= cx1 and cz2 >= cz1:
        seq["centre"](d, cx1, cz1, cx2, cz2, y, free)
    # lights
    ly = y + 3
    for x in range(ix1 + 1, ix2, 4):
        for z in range(iz1 + 1, iz2, 4):
            xx, zz = x + 1 if x + 1 <= ix2 else x, z + 1 if z + 1 <= iz2 else z
            if (xx, zz) in res or not d.air(xx, ly, zz):
                continue
            if d.get(xx, ly + 1, zz) != AIR:
                d.set(xx, ly, zz, lamp if P != "Neoterra" else "end_rod[facing=down]")
                if P == "Neoterra" and "concrete" in d.get(xx, ly + 1, zz):
                    d.set(xx, ly + 1, zz, "pearlescent_froglight[axis=y]")
                    d.set(xx, ly, zz, AIR)
            elif top and d.get(xx, ly + 2, zz) != AIR and d.air(xx, ly + 1, zz):
                d.set(xx, ly + 1, zz, "chain[axis=y,waterlogged=false]")
                d.set(xx, ly, zz, lamp if P != "Neoterra" else "end_rod[facing=down]")
            elif top and d.get(xx, ly + 1, zz) == AIR:
                for k in range(1, 6):
                    if d.bp.inside(xx, ly + k, zz) and d.get(xx, ly + k, zz) != AIR:
                        for kk in range(1, k):
                            d.set(xx, ly + kk, zz, "chain[axis=y,waterlogged=false]")
                        d.set(xx, ly, zz, lamp if P != "Neoterra" else "end_rod[facing=down]")
                        break
    # rug in the aisle-free middle
    rugc = {"Hearthwood": ("red_carpet", "orange_carpet"), "Cascadia": ("brown_carpet", "green_carpet"),
            "Neoterra": ("light_gray_carpet", "cyan_carpet")}[P]
    if seq.get("rug", True) and cx2 - cx1 >= 0 and cz2 - cz1 >= 0:
        for x in range(cx1 - 1, cx2 + 2):
            for z in range(cz1 - 1, cz2 + 2):
                if (x, z) not in res and d.air(x, y, z) and d.get(x, y - 1, z) != AIR and \
                        not any("_bed" in d.get(x + a, y, z + b) for a, b in ((0, 0),)):
                    edge = x in (cx1 - 1, cx2 + 1) or z in (cz1 - 1, cz2 + 1)
                    d.set(x, y, z, rugc[0] if edge else rugc[1])


# ring item makers: f(d, x, y, z, facing_into_room, tall_ok)
def _slab_with(top):
    def f(d, x, y, z, face, tall):
        d.set(x, y, z, SL(_w(d), "top"))
        t = top(face) if callable(top) else top
        if t:
            d.set(x, y + 1, z, t)
    return f


def _w(d):
    return {"Hearthwood": "dark_oak", "Cascadia": "spruce", "Neoterra": "birch"}[d.pack]


def _blk(b):
    def f(d, x, y, z, face, tall):
        d.set(x, y, z, b(face) if callable(b) else b)
    return f


def _stack(lo, hi):
    def f(d, x, y, z, face, tall):
        d.set(x, y, z, lo(face) if callable(lo) else lo)
        if tall:
            d.set(x, y + 1, z, hi(face) if callable(hi) else hi)
    return f


def _shelf3(d, x, y, z, face, tall):
    if tall:
        d.bookshelf(x, y, z, 3)
    else:
        d.bookshelf(x, y, z, 1)


def _chisel(face):
    return (f"chiseled_bookshelf[facing={face},slot_0_occupied=true,slot_1_occupied=false,slot_2_occupied=true,"
            f"slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")


def _rack_weapons(d, x, y, z, face, tall):
    d.set(x, y, z, SL(_w(d), "top"))
    d.set(x, y + 1, z, ROD())
    ox, oz = D4[OPP[face]]
    if tall and d.air(x, y + 2, z):
        d.set(x, y + 2, z, f"{['red', 'white', 'blue', 'green'][(x + z) % 4]}_wall_banner[facing={face}]")


def _bed_single(d, x, y, z, face, tall):
    fx, fz = D4[face]
    if d.air(x + fx, y, z + fz) and d.get(x + fx, y - 1, z + fz) != AIR:
        d.bed(x, y, z, OPP[face])


def _chair_to(face_dir):
    pass


def _desk(d, x, y, z, face, tall):
    d.set(x, y, z, SL(_w(d), "top"))
    d.candle(x, y + 1, z, 1 + (x + z) % 3)
    fx, fz = D4[face]
    if d.air(x + fx, y, z + fz) and d.get(x + fx, y - 1, z + fz) != AIR:
        pass


def _pots(face):
    return "decorated_pot[cracked=false,facing=%s,waterlogged=false]" % face


def _keg(face):
    return f"barrel[facing={face},open=false]"


def _table_rows(chairs=True, top=None, along=None, step=2):
    def c(d, cx1, cz1, cx2, cz2, y, free):
        wood = _w(d)
        long_x = (cx2 - cx1) >= (cz2 - cz1)
        if long_x:
            zc = (cz1 + cz2) // 2
            for x in range(cx1, cx2 + 1):
                if free(x, zc):
                    d.table(x, y, zc, wood, "post") if top is None else d.set(x, y, zc, top)
                    if chairs:
                        for dz, back in ((-1, "north"), (1, "south")):
                            if free(x, zc + dz) and (x - cx1) % step == 0:
                                d.chair(x, y, zc + dz, back, wood, sit=False)
        else:
            xc = (cx1 + cx2) // 2
            for z in range(cz1, cz2 + 1):
                if free(xc, z):
                    d.table(xc, y, z, wood, "post") if top is None else d.set(xc, y, z, top)
                    if chairs:
                        for dx, back in ((-1, "west"), (1, "east")):
                            if free(xc + dx, z) and (z - cz1) % step == 0:
                                d.chair(xc + dx, y, z, back, wood, sit=False)
    return c


def _dummies(d, cx1, cz1, cx2, cz2, y, free):
    for x in range(cx1, cx2 + 1, 3):
        for z in range(cz1, cz2 + 1, 3):
            if free(x, z, 3):
                dummy(d, x, y, z, "north")


def _bunks(d, cx1, cz1, cx2, cz2, y, free):
    pass


KINDS = {
    "bunks": lambda d, w: dict(ring=[_bed_single, _slab_with(lambda f: "candle[candles=1,lit=false,waterlogged=false]"),
                                     _bed_single, _blk(lambda f: f"chest[facing={f},type=single,waterlogged=false]")],
                               rug=True),
    "mess": lambda d, w: dict(ring=[_blk(_keg), _stack(_keg, _keg), _slab_with(_pots), _blk("smoker[facing=north,lit=false]"),
                                    _slab_with("potted_red_mushroom"), _blk(lambda f: f"barrel[facing=up,open=false]")],
                              centre=_table_rows(True), rug=False),
    "armoury": lambda d, w: dict(ring=[_rack_weapons, _rack_weapons, _blk(lambda f: f"grindstone[face=floor,facing={f}]"),
                                       _rack_weapons, _blk(lambda f: f"chest[facing={f},type=single,waterlogged=false]"),
                                       _blk("smithing_table")], centre=_dummies, rug=False),
    "office": lambda d, w: dict(ring=[_desk, _blk(_chisel), _blk("cartography_table"), _slab_with(lambda f: FLOWERS[3]),
                                      _blk(_chisel), _stack(_keg, "potted_fern")],
                                centre=_table_rows(True, step=1)),
    "library": lambda d, w: dict(ring=[_shelf3, _shelf3, _shelf3, _blk(_chisel)], centre=_table_rows(True)),
    "store": lambda d, w: dict(ring=[_stack(_keg, _keg), _blk("brown_wool"), _stack(_keg, "white_wool"),
                                     _blk(lambda f: f"chest[facing={f},type=single,waterlogged=false]"),
                                     _stack("hay_block[axis=y]", _keg)], rug=False),
    "lab": lambda d, w: dict(ring=[_slab_with("brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]"),
                                   _slab_with(_pots), _blk("water_cauldron[level=2]"),
                                   _slab_with(lambda f: FLOWERS[5]), _blk(_chisel)],
                             centre=_table_rows(False)),
    "workshop": lambda d, w: dict(ring=[_blk("crafting_table"), _blk(lambda f: f"furnace[facing={f},lit=false]"),
                                        _stack(_keg, "lantern[hanging=false,waterlogged=false]"),
                                        _blk("smithing_table"), _blk(lambda f: f"grindstone[face=floor,facing={f}]"),
                                        _blk("fletching_table")], centre=_table_rows(False), rug=False),
    "lounge": lambda d, w: dict(ring=[_blk(_chisel), _slab_with(lambda f: FLOWERS[0]), _shelf3,
                                      _slab_with(_pots), _blk(lambda f: f"jukebox[has_record=false]")],
                                centre=_table_rows(True, step=1)),
    "kitchen": lambda d, w: dict(ring=[_blk(lambda f: f"smoker[facing={f},lit=false]"), _slab_with(_pots),
                                       _blk("water_cauldron[level=3]"), _blk(lambda f: f"furnace[facing={f},lit=false]"),
                                       _stack(_keg, _keg), _slab_with("potted_red_mushroom")],
                                 centre=_table_rows(True)),
    "gym": lambda d, w: dict(ring=[_rack_weapons, _stack("hay_block[axis=y]", "target[power=0]"),
                                   _blk(lambda f: f"barrel[facing=up,open=false]")], centre=_dummies, rug=False),
    "chapel": lambda d, w: dict(ring=[_slab_with("candle[candles=3,lit=false,waterlogged=false]"), None,
                                      _slab_with(lambda f: FLOWERS[2])], centre=_table_rows(True)),
    "greenhouse": lambda d, w: dict(ring=[_blk("moss_block"), _blk("flowering_azalea"), _blk("moss_block"),
                                          _slab_with(lambda f: FLOWERS[1])], rug=False),
    None: None,
}


# ---------------------------------------------------------------------------------------------- exterior kit
def lamp_post(d, x, z, y=2):
    P = d.pack
    if P == "Neoterra":
        for yy in range(y, y + 3):
            d.set(x, yy, z, "iron_bars" if yy < y + 2 else "light_gray_concrete")
        d.set(x, y + 3, z, "sea_lantern")
        d.set(x, y + 4, z, SL("smooth_quartz"))
    else:
        f = "dark_oak_fence" if P == "Hearthwood" else "spruce_fence"
        for yy in range(y, y + 3):
            d.set(x, yy, z, f)
        d.set(x, y + 3, z, LANT_S)


def bench(d, x, z, back, n=2, y=2):
    dx, dz = (1, 0) if back in ("north", "south") else (0, 1)
    for i in range(n):
        d.chair(x + dx * i, y, z + dz * i, back, _w(d), sit=False)


def path(d, x1, z1, x2, z2, border=True):
    P = d.pack
    m = {"Hearthwood": "gravel", "Cascadia": "coarse_dirt", "Neoterra": "smooth_stone"}[P]
    bm = {"Hearthwood": "stone_bricks", "Cascadia": "cobblestone", "Neoterra": "polished_andesite"}[P]
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for z in range(min(z1, z2), max(z1, z2) + 1):
            d.set(x, 1, z, m)


def flowerbed(d, x1, z1, x2, z2, y=2):
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if d.air(x, y, z):
                d.set(x, y - 1, z, "grass_block[snowy=false]")
                d.set(x, y, z, ["poppy", "oxeye_daisy", "cornflower", "allium", "azure_bluet", "dandelion",
                                "short_grass"][(x * 7 + z * 3) % 7])


def hedge(d, x1, z1, x2, z2, y=2, leaves="oak_leaves"):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for z in range(min(z1, z2), max(z1, z2) + 1):
            if d.air(x, y, z):
                d.set(x, y, z, f"{leaves}[distance=1,persistent=true,waterlogged=false]")


def cart(d, x, z, axis="x", y=2):
    """Hand cart: plank bed on a wheel axle with a crate and a sack."""
    P = d.pack
    w = "spruce" if P != "Neoterra" else "birch"
    dx, dz = (1, 0) if axis == "x" else (0, 1)
    for i in range(2):
        d.set(x + dx * i, y, z + dz * i, SL(w, "top"))
    d.set(x + dx * 2, y, z + dz * 2, f"{w}_fence")
    d.set(x, y + 1, z, "barrel[facing=up,open=false]")
    d.set(x + dx, y + 1, z + dz, "hay_block[axis=y]" if P != "Neoterra" else "white_wool")
    sx, sz = (0, 1) if axis == "x" else (1, 0)
    for s in (-1, 1):
        if d.air(x + sx * s, y, z + sz * s):
            d.set(x + sx * s, y, z + sz * s, TD(w, ("south" if s > 0 else "north") if axis == "x"
                                                 else ("east" if s > 0 else "west"), "bottom", "true"))


# ================================================================================================ GUARD TOWER
def gt_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (44, 26, 24))
    x1, z1, x2, z2 = 3, 4, 9, 10
    # ground storey: rubble-faced stone brick
    d.box(x1, 2, z1, x2, 5, z2, "stone_bricks", floor="spruce_planks")
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if (x in (x1, x2) or z in (z1, z2)) and (x * 5 + z * 3) % 7 == 0:
                d.set(x, 3 + (x + z) % 3, z, "mossy_stone_bricks")
            if (x in (x1, x2) or z in (z1, z2)):
                d.set(x, 1, z, "cobblestone")
    d.fill(x1, 6, z1, x2, 6, z2, "dark_oak_planks")
    hw_frame(d, x1, z1, x2, z2, 7, 10)
    top = 11
    # arrow slits below, leaded windows above
    for z in (6, 8):
        d.window(x1, 3, z, x1, 4, z)
    d.window(x2, 3, 6, x2, 4, 6)
    for x in (5, 7):
        d.window(x, 3, z2, x, 4, z2)
    for x in (5, 7):
        d.window(x, 8, z1, x, 9, z1)
        d.window(x, 8, z2, x, 9, z2)
    d.window(x1, 8, 7, x1, 9, 7)
    d.door(6, 2, z1, "south", "dark_oak")
    d.set(6, 4, z1, "chiseled_stone_bricks")
    d.set(5, 4, z1 - 1, "wall_torch[facing=north]")
    d.set(7, 4, z1 - 1, "wall_torch[facing=north]")
    # ladder in the south-east corner, all floors
    lx, lz = x2 - 1, z2 - 1
    # ---- guard room
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x2 - 1, 2, z1 + 1, "barrel")
    d.set(x2 - 1, 3, z1 + 1, "decorated_pot[cracked=false,facing=west,waterlogged=false]")
    weapon_rack(d, x2 - 1, z1 + 2, x2 - 1, z1 + 3, 2, "dark_oak", "west")
    d.banner(x2 - 1, 4, z1 + 3, "west", "red")
    d.dining(5, 2, 7, 2, "z", "dark_oak", ("w",), sit=False)
    d.chair(6, 2, 7, "east", "dark_oak", sit=False)
    d.lamp(6, 5, 7)
    d.set(x1 + 1, 2, z2 - 1, "smithing_table")
    d.banner(x1 + 1, 4, z2 - 1, "east", "red")
    # ---- bunk room
    d.bed(x1 + 1, 7, z1 + 1, "west")
    d.bed(x1 + 1, 7, z1 + 4, "west")
    d.set(x1 + 1, 7, z1 + 2, SL("dark_oak", "top"))
    d.candle(x1 + 1, 8, z1 + 2, 2)
    d.set(x1 + 1, 7, z1 + 3, "chest[facing=east,type=single,waterlogged=false]")
    d.set(x2 - 1, 7, z1 + 1, "chiseled_bookshelf[facing=west,slot_0_occupied=true,slot_1_occupied=false,"
                             "slot_2_occupied=true,slot_3_occupied=false,slot_4_occupied=false,slot_5_occupied=true]")
    d.rug(x1 + 3, z1 + 2, x1 + 4, z1 + 4, 7, ("red_carpet",), "plain")
    d.lamp(6, 10, 6)
    if L == 1:
        ladder(d, lx, lz, 2, 6, "west")
        hipcap(d, x1, z1, x2, z2, top, "deepslate_tile_stairs", "deepslate_tile_slab", "dark_oak_planks")
    else:
        # open lookout storey with corner posts, rail and alarm bell
        ladder(d, lx, lz, 2, 11, "west")
        d.set(x2, 7, lz, "stripped_dark_oak_log[axis=y]")
        d.fill(x1, 11, z1, x2, 11, z2, "dark_oak_planks")
        d.set(lx, 11, lz, "ladder[facing=west,waterlogged=false]")
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if x in (x1, x2) or z in (z1, z2):
                    post = (x in (x1, x2, 6)) and (z in (z1, z2, 7))
                    d.set(x, 12, z, LOG("stripped_dark_oak_log") if post else "dark_oak_fence")
                    d.set(x, 13, z, LOG("stripped_dark_oak_log") if post else AIR)
                    d.set(x, 14, z, LOG("stripped_dark_oak_log", "x" if z in (z1, z2) else "z"))
        d.set(x2, 12, lz, "stripped_dark_oak_log[axis=y]")
        hipcap(d, x1, z1, x2, z2, 15, "deepslate_tile_stairs", "deepslate_tile_slab", "dark_oak_planks")
        d.set(6, 14, 7, "bell[attachment=ceiling,facing=north,powered=false]")
        d.chair(x1 + 1, 12, z1 + 1, "west", "dark_oak", sit=False)
    # ---- L2+: guardroom with a mess (L3+ barracks storey above) east of the tower
    if L >= 2:
        d.set(x2, 2, 7, AIR)
        d.set(x2, 3, 7, AIR)
        building(d, 10, 4, 19, 10, nf=1 if L < 3 else 2, axis="x", doors=(("north", 15), ("west", 7)),
                 chimney=(20, 7), kinds=["mess", "bunks"])
        d.sign(13, 4, 3, "north", ["Watch", "House"], "dark_oak")
        path(d, 15, 0, 15, 3)
        bench(d, 11, 3, "south", 2)
        lamp_post(d, 18, 2)
    if L >= 3:
        # armoury and smithy behind, drill yard beside it
        building(d, 10, 13, 19, 19, nf=1, axis="x", doors=(("north", 14), ("west", 16)), chimney=(20, 16),
                 kinds=["armoury"])
        yx1, yz1, yx2, yz2 = 1, 13, 8, 21
        d.fill(yx1, 1, yz1, yx2, 1, yz2, "coarse_dirt")
        for x in range(yx1, yx2 + 1):
            for z in range(yz1, yz2 + 1):
                if x in (yx1, yx2) or z in (yz1, yz2):
                    d.set(x, 2, z, "dark_oak_fence")
        d.set(yx2, 2, 16, "dark_oak_fence_gate[facing=east,in_wall=false,open=false,powered=false]")
        d.set(5, 2, yz1, "dark_oak_fence_gate[facing=north,in_wall=false,open=false,powered=false]")
        for x in (3, 6):
            dummy(d, x, 2, 19, "north")
        d.set(3, 2, 15, "hay_block[axis=x]")
        d.set(3, 3, 15, "target[power=0]")
        d.set(7, 2, 14, "water_cauldron[level=3]")
        for x, z in ((yx1, yz1), (yx2, yz1), (yx1, yz2), (yx2, yz2)):
            d.set(x, 3, z, LANT_S)
        path(d, 9, 11, 9, 21)
        path(d, 5, 11, 9, 12)
        cart(d, 15, 21, "x")
    if L >= 4:
        # barracks hall
        building(d, 23, 4, 34, 11, nf=2, axis="x", doors=(("north", 28), ("west", 8)), chimney=(35, 8),
                 kinds=["mess", "bunks"])
        path(d, 28, 0, 28, 3)
        flowerbed(d, 23, 1, 26, 2)
        flowerbed(d, 31, 1, 34, 2)
    if L >= 5:
        # stable and a gate tower round a cobbled court
        building(d, 23, 15, 34, 21, nf=2, axis="x", doors=(("north", 26), ("north", 31)), kinds=["store", "store"])
        building(d, 37, 4, 43, 10, nf=3, roof="hip", doors=(("north", None),), ground="stone_bricks",
                 kinds=["office", "bunks", "armoury"])
        d.banner(40, 13, 3, "north", "red")
        d.fill(20, 1, 12, 37, 1, 14, "cobblestone")
        for x in (21, 37):
            lamp_post(d, x, 13)
        d.set(36, 2, 18, "water_cauldron[level=3]")
        d.set(36, 2, 19, "hay_block[axis=y]")
        d.set(36, 2, 20, "hay_block[axis=y]")
        d.set(36, 3, 20, "hay_block[axis=x]")
        bench(d, 25, 13, "south", 3)
        # jettied lookout gallery round the tower's lookout storey
        for x in range(x1 - 1, x2 + 2):
            for z in range(z1 - 1, z2 + 2):
                if x in (x1 - 1, x2 + 1) or z in (z1 - 1, z2 + 1):
                    if d.air(x, 11, z):
                        d.set(x, 11, z, "dark_oak_planks")
                        d.set(x, 12, z, "dark_oak_fence")
        for z in (z1, z2):
            d.set(6, 12, z, AIR)
        d.banner(6, 9, z1 - 1, "north", "red")
        d.banner(x1 - 1, 9, 7, "west", "red")
    # village dressing round the tower
    flowerbed(d, 1, 4, 1, 10)
    lamp_post(d, 2, 2)
    return d


def gt_cascadia(rel, L):
    d = Design("Cascadia", rel, (41, 32, 35), paving="coarse_dirt")
    # bunk cabin
    x1, z1, x2, z2 = 2, 6, 10, 12
    cs_walls(d, x1, z1, x2, z2, 2, 5)
    d.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, z2 - 1, "spruce_planks")
    d.door(6, 2, z1, "south", "spruce")
    d.window(4, 3, z1, 4, 4, z1)
    d.window(8, 3, z1, 8, 4, z1)
    d.window(x2, 3, 9, x2, 4, 9)
    d.window(6, 3, z2, 6, 4, z2)
    ridge = cs_roof(d, x1, z1, x2, z2, 6, "x", "spruce_planks")
    d.fill(x1 + 1, 6, z1 + 1, x2 - 1, 6, z2 - 1, "spruce_planks")
    # stone chimney on the west gable
    d.hearth(x1 + 1, 2, 9, "east", 6, "cobblestone", "campfire")
    for y in range(1, ridge + 2):
        d.set(x1, y, 9, "mossy_cobblestone" if y % 3 == 0 else "cobblestone")
    d.set(x1 - 1, 1, 9, "cobblestone")
    # porch
    for x in range(x1, x2 + 1):
        for z in range(z1 - 3, z1):
            d.set(x, 1, z, "spruce_planks")
        d.set(x, 5, z1 - 3, ST("spruce", "south"))
        for z in range(z1 - 2, z1):
            d.set(x, 5, z, SL("spruce", "top"))
    for x in (x1, x2):
        for y in range(2, 5):
            d.set(x, y, z1 - 3, LOG("spruce_log"))
    for x in range(x1 + 1, x2):
        if x not in (5, 6, 7):
            d.set(x, 2, z1 - 3, "spruce_fence")
    d.chair(x1 + 1, 2, z1 - 1, "south", "spruce", sit=False)
    d.keg(x2 - 1, 2, z1 - 1, "north")
    d.lamp(6, 4, z1 - 2)
    # inside
    d.hut(x1 + 2, 2, z1 + 1)
    d.item(x2 - 1, 2, z1 + 1, "barrel")
    d.bed(x1 + 2, 2, z2 - 1, "south")
    d.bed(x2 - 1, 2, z2 - 1, "south")
    d.set(x2 - 2, 2, z2 - 1, SL("spruce", "top"))
    d.set(x2 - 2, 3, z2 - 1, LANT_S)
    d.table(6, 2, 9, "spruce")
    d.chair(6, 2, 8, "north", "spruce", sit=False)
    d.chair(7, 2, 9, "east", "spruce", sit=False)
    d.rug(4, 8, 8, 10, 2, ("brown_carpet", "green_carpet"))
    weapon_rack(d, x2 - 1, 8, x2 - 1, 8, 2, "spruce", "west")
    d.lamp(6, 5, 9)
    # trestle lookout tower
    tx1, tz1, tx2, tz2 = 14, 7, 18, 11
    yc = {1: 9, 2: 12, 3: 15, 4: 18, 5: 21}[L]
    for x, z in ((tx1, tz1), (tx2, tz1), (tx1, tz2), (tx2, tz2)):
        d.set(x, 1, z, "cobblestone")
        for y in range(2, yc):
            d.set(x, y, z, LOG("spruce_log"))
    for y in range(4, yc, 3):                                     # girts and sway bracing
        for x in range(tx1 + 1, tx2):
            for z in (tz1, tz2):
                d.set(x, y, z, LOG("stripped_spruce_log", "x"))
        for z in range(tz1 + 1, tz2):
            for x in (tx1, tx2):
                d.set(x, y, z, LOG("stripped_spruce_log", "z"))
        for k in range(1, 4):
            if y + k < yc - 1:
                for x, z in ((tx1 + k, tz1), (tx2 - k, tz2), (tx1, tz1 + k), (tx2, tz2 - k)):
                    d.set(x, y + k, z, "spruce_fence")
    mx = (tx1 + tx2) // 2
    for y in range(2, yc):
        d.set(mx, y, tz1 + 3, LOG("spruce_log"))
    d.set(mx, 1, tz1 + 3, "cobblestone")
    ladder(d, mx, tz1 + 2, 2, yc, "north")
    # cab + catwalk
    d.fill(tx1 - 1, yc, tz1 - 1, tx2 + 1, yc, tz2 + 1, "spruce_planks")
    for x in range(tx1 - 1, tx2 + 2):
        for z in range(tz1 - 1, tz2 + 2):
            if x in (tx1 - 1, tx2 + 1) or z in (tz1 - 1, tz2 + 1):
                d.set(x, yc + 1, z, "spruce_fence")
                if (x + z) % 2 == 0:
                    d.set(x, yc - 1, z, ST("spruce", OPP["north" if z == tz1 - 1 else "south" if z == tz2 + 1 else "west" if x == tx1 - 1 else "east"], "top"))
    d.set(mx, yc, tz1 + 2, "ladder[facing=north,waterlogged=false]")
    cx1, cz1, cx2, cz2 = tx1, tz1, tx2, tz2
    cs_walls(d, cx1, cz1, cx2, cz2, yc + 1, yc + 3, footing=False)
    for x in range(cx1 + 1, cx2):
        d.window(x, yc + 2, cz1, x, yc + 3, cz1)
        d.window(x, yc + 2, cz2, x, yc + 3, cz2)
    for z in range(cz1 + 1, cz2):
        d.window(cx1, yc + 2, z, cx1, yc + 3, z)
        d.window(cx2, yc + 2, z, cx2, yc + 3, z)
    d.door(cx1 + 1, yc + 1, cz1, "south", "spruce")
    hipcap(d, cx1, cz1, cx2, cz2, yc + 4, "deepslate_tile_stairs", "deepslate_tile_slab", "spruce_planks")
    d.set(mx + 1, yc + 1, tz1 + 2, "cartography_table")             # fire finder
    d.set(mx, yc + 1, tz1 + 3, "spruce_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
    d.lamp(mx, yc + 3, tz1 + 2)
    cs_trim(d, x1, z1, x2, z2, 2, 5)
    d.sign(6, 4, z1 - 1, "north", ["RANGER", "STATION"], "spruce")
    for x in range(x1 + 1, x2):                                   # window boxes
        if d.get(x, 3, z1) == "minecraft:glass_pane":
            d.set(x, 2, z1 - 1, "spruce_trapdoor[facing=north,half=top,open=true,powered=false,waterlogged=false]") if False else None
    if L >= 3:
        # woodshed lean-to behind the cabin with a woodpile
        for x in range(x1 + 1, x2):
            d.set(x, 1, z2 + 1, "spruce_planks")
            d.set(x, 1, z2 + 2, "spruce_planks")
            d.set(x, 4, z2 + 3, ST("spruce", "north"))
            for z in (z2 + 1, z2 + 2):
                d.set(x, 5, z, SL("spruce"))
            if x % 2:
                d.set(x, 2, z2 + 1, LOG("spruce_log", "x"))
                d.set(x, 3, z2 + 1, LOG("oak_log", "x"))
            else:
                d.set(x, 2, z2 + 1, LOG("birch_log", "x"))
        for x in (x1 + 1, x2 - 1):
            for y in range(2, 4):
                d.set(x, y, z2 + 3, LOG("spruce_log"))
        d.set(x2 - 2, 2, z2 + 2, "chipped_anvil[facing=east]") if False else None
    if L >= 4:
        # rain-water tank on stilts and a split-rail fence round the site
        for x, z in ((13, 15), (15, 15), (13, 17), (15, 17)):
            for y in range(2, 5):
                d.set(x, y, z, "spruce_fence")
        d.fill(13, 5, 15, 15, 5, 17, "spruce_planks")
        for x in range(13, 16):
            for z in range(15, 18):
                if (x, z) != (14, 16):
                    d.set(x, 6, z, LOG("stripped_spruce_log", "x" if z != 16 else "z"))
        d.set(14, 6, 16, "water_cauldron[level=3]")
        for x in range(0, 23):
            if x not in (5, 6, 7):
                d.set(x, 2, 1, "spruce_fence" if x % 4 else "spruce_log[axis=y]")
    if L >= 5:
        for y in range(yc + 5, yc + 9):
            d.set(mx, y, tz1 + 2, "spruce_fence")
        d.set(mx, yc + 8, tz1 + 1, "red_wall_banner[facing=north]")
        d.set(tx2 + 1, yc + 1, tz1 + 2, "bell[attachment=floor,facing=east,powered=false]")
    # ---- growth: a ranger station complex
    if L >= 2:                                                    # equipment shed with a work porch
        building(d, 23, 4, 31, 10, nf=1, axis="z", doors=(("north", 27), ("west", 7)), kinds=["workshop"])
        for z in range(5, 10):
            d.set(22, 1, z, "spruce_planks")
        cart(d, 33, 6, "z")
        lamp_post(d, 21, 3)
        path(d, 12, 13, 26, 13)
    if L >= 3:                                                    # two-storey bunkhouse
        building(d, 21, 16, 33, 23, nf=2, axis="x", doors=(("north", 27), ("west", 19)), chimney=(34, 20),
                 kinds=["mess", "bunks"])
        for x in range(21, 34):                                   # porch along the front
            d.set(x, 1, 15, "spruce_planks")
            d.set(x, 1, 14, "spruce_planks")
            d.set(x, 5, 14, ST("spruce", "north"))
            d.set(x, 5, 15, SL("spruce", "top"))
        for x in (21, 25, 29, 33):
            for y in range(2, 5):
                d.set(x, y, 14, LOG("spruce_log"))
        bench(d, 22, 15, "south", 2)
        bench(d, 31, 15, "south", 2)
    if L >= 4:                                                    # horse barn and corral
        building(d, 2, 21, 12, 31, nf=2, axis="z", doors=(("north", 7), ("east", 25)), kinds=["store", "store"])
        for x in range(14, 20):
            for z in range(25, 32):
                if x in (14, 19) or z in (25, 31):
                    d.set(x, 2, z, "spruce_fence")
        d.set(14, 2, 27, "spruce_fence_gate[facing=east,in_wall=false,open=false,powered=false]")
        d.set(17, 2, 29, "water_cauldron[level=3]")
        d.set(16, 2, 30, "hay_block[axis=y]")
        tree(d, 37, 2, 3, "spruce_log", "spruce_leaves", 7, 2, cone=True)
    if L >= 5:                                                    # radio room / mess hall and a second lookout
        building(d, 21, 26, 37, 32, nf=2, axis="x", doors=(("north", 29), ("north", 24)), chimney=(29, 33),
                 kinds=["kitchen", "office"])
        t2 = building(d, 35, 8, 39, 12, nf=4, roof="hip", doors=(("west", None),),
                      kinds=["office", "store", "office", "office"], stairs=False)
        ladder(d, 38, 11, 2, 17, "north")
        for y in range(t2.ridge + 1, t2.ridge + 4):
            d.set(37, y, 10, "iron_bars")
        d.set(37, t2.ridge + 4, 10, ROD())
        tree(d, 37, 2, 22, "spruce_log", "spruce_leaves", 8, 2, cone=True)
        tree(d, 2, 2, 31, "spruce_log", "spruce_leaves", 7, 2, cone=True)
    return d


def gt_neoterra(rel, L):
    d = Design("Neoterra", rel, (44, 34, 36), paving="smooth_stone")
    x1, z1, x2, z2 = 2, 3, 13, 9
    nt_walls(d, x1, z1, x2, z2, 2, 5)
    d.fill(x1, 1, z1, x2, 1, z2, "polished_diorite")
    d.flat(x1, z1 - 1, x2, z2, 6, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
    for x in range(x1, x2 + 1):
        d.set(x, 6, z1 - 1, "cyan_terracotta")
    for x in range(x1 + 1, x2):
        d.window(x, 2, z1, x, 5, z1, "glass_pane")
    for x in (6, 10):
        d.set(x, 2, z1, "light_gray_concrete")
        for y in range(3, 6):
            d.set(x, y, z1, "light_gray_concrete")
    d.double_door(7, 2, z1, "x", "south", "birch")
    d.sign(10, 5, z1 - 1, "north", ["", "SECURITY", "POST"], "birch", glow=True, color="cyan")
    # shaft
    sx1, sz1, sx2, sz2 = 6, 9, 10, 13
    yp = 7 + 3 * L
    nt_walls(d, sx1, sz1, sx2, sz2, 2, yp - 1, "light_gray_concrete", "gray_concrete")
    d.fill(sx1 + 1, 1, sz1 + 1, sx2 - 1, 1, sz2 - 1, "polished_diorite")
    for y in range(3, yp - 1):
        d.set(8, y, sz2, "cyan_stained_glass")
    d.set(8, 2, sz1, AIR)
    d.set(8, 3, sz1, AIR)
    ladder(d, 8, sz2 - 1, 2, yp, "north")
    # pod
    px1, pz1, px2, pz2 = 4, 7, 12, 15
    d.fill(px1, yp, pz1, px2, yp, pz2, "light_gray_concrete")
    d.set(8, yp, sz2 - 1, "ladder[facing=north,waterlogged=false]")
    nt_walls(d, px1, pz1, px2, pz2, yp + 1, yp + 3, "light_gray_stained_glass_pane", "white_concrete")
    d.flat(px1, pz1, px2, pz2, yp + 4, "white_concrete", "smooth_quartz", None)
    for x in range(px1, px2 + 1):
        for z in (pz1, pz2):
            d.set(x, yp, z, "cyan_terracotta")
    for z in range(pz1, pz2 + 1):
        for x in (px1, px2):
            d.set(x, yp, z, "cyan_terracotta")
    for x in range(px1 + 1, px2):                                # console desk along the street glass
        d.set(x, yp + 1, pz1 + 1, SL("smooth_quartz", "top"))
        if x % 2:
            d.set(x, yp + 2, pz1 + 1, "black_stained_glass_pane")
    for x in (6, 8, 10):
        d.chair(x, yp + 1, pz1 + 2, "south", "birch", sit=False)
    d.set(px1 + 2, yp + 1, pz2 - 2, "cartography_table")
    d.set(px2 - 1, yp + 1, pz2 - 1, "potted_bamboo")
    for x in (6, 10):
        d.set(x, yp + 3, 11, "sea_lantern")
        d.set(x, yp + 3, 11, AIR)
        d.set(x, yp + 4, 11, "sea_lantern")
    # antenna and beacon
    for y in range(yp + 6, yp + 9):
        d.set(8, y, 11, "iron_bars")
    d.set(8, yp + 5, 11, "sea_lantern")
    d.set(8, yp + 9, 11, ROD())
    # lobby
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x1 + 1, 2, z2 - 1, "barrel")
    for x in (x1 + 2, x1 + 3):                                  # lockers
        d.set(x, 2, z2 - 1, "iron_block")
        d.set(x, 3, z2 - 1, "iron_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]")
    for z in range(z1 + 2, z1 + 5):                             # front desk with screens
        d.set(5, 2, z, "smooth_quartz")
        if z != z1 + 3:
            d.set(5, 3, z, "black_stained_glass_pane")
    d.chair(4, 2, z1 + 3, "west", "birch", sit=False)
    # crew room behind a glass partition
    for z in range(z1 + 1, z2):
        d.set(10, 2, z, "white_concrete" if z == z1 + 1 else "light_gray_stained_glass_pane")
        for y in (3, 4):
            d.set(10, y, z, "light_gray_stained_glass_pane")
        d.set(10, 5, z, "white_concrete")
    d.door(10, 2, z1 + 3, "east", "birch")
    d.bed(x2 - 1, 2, z1 + 1, "east")
    d.bed(x2 - 1, 2, z2 - 1, "east")
    d.set(x2 - 1, 2, z1 + 3, "white_concrete")
    d.set(x2 - 1, 3, z1 + 3, "end_rod[facing=up]")
    for x in range(x1 + 2, x2, 3):
        d.set(x, 5, 6, "sea_lantern")
    d.window(x1, 3, 6, x1, 4, 7, "glass_pane")
    d.window(x2, 3, 5, x2, 4, 7, "glass_pane")
    if L >= 3:                                                  # roof terrace on the lobby
        for x in range(x1 + 1, x2):
            d.set(x, 7, z1, "azalea" if x % 3 == 0 else "moss_block")
        d.set(x1 + 1, 7, z1 + 3, "white_concrete")
        for z in range(z1 + 1, z1 + 5, 2):
            d.chair(x1 + 2, 7, z, "west", "birch", sit=False)
        d.set(x1 + 3, 7, z1 + 2, SL("smooth_quartz", "top"))
        ladder(d, x1 - 1, z1 + 2, 2, 6, "west")
        d.set(x1, 7, z1 + 2, AIR)
        d.set(x1, 8, z1 + 2, AIR)
    if L >= 4:                                                  # armoury wing
        ax1, ax2 = 14, 19
        nt_walls(d, ax1, 5, ax2, 12, 2, 5)
        d.fill(ax1, 1, 5, ax2, 1, 12, "polished_diorite")
        d.flat(ax1, 5, ax2, 12, 6, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
        d.set(ax1, 2, 7, AIR) if False else None
        d.door(16, 2, 5, "south", "birch")
        d.window(18, 3, 5, 18, 4, 5, "glass_pane")
        for z in range(7, 11, 2):
            d.window(ax2, 3, z, ax2, 4, z, "glass_pane")
        weapon_rack(d, ax1 + 1, 8, ax1 + 1, 11, 2, "birch", "east")
        for z in (8, 10):
            d.banner(ax1 + 1, 4, z, "east", "cyan")
        d.set(ax2 - 1, 2, 11, "smithing_table")
        d.set(ax2 - 1, 2, 10, "grindstone[face=floor,facing=west]")
        d.set(17, 5, 9, "sea_lantern")
    if L >= 5:                                                  # helipad markings on the pod roof
        for x in range(px1 + 1, px2):
            for z in range(pz1 + 1, pz2):
                if (x in (6, 10) and 9 <= z <= 13) or (z == 11 and 6 <= x <= 10):
                    d.set(x, yp + 4, z, "yellow_concrete")
        d.set(8, yp + 4, 11, "white_concrete")
    # ---- growth: a security campus
    if L >= 2:                                                    # vehicle bay / checkpoint
        building(d, 23, 3, 33, 10, nf=1, roof="flat", doors=(("north", 26), ("west", 7)), kinds=["workshop"])
        for x in range(28, 33):
            for y in (2, 3, 4):
                d.set(x, y, 3, "iron_bars" if y < 4 else "light_gray_concrete")
        cart(d, 35, 5, "z")
        lamp_post(d, 21, 1)
        lamp_post(d, 35, 1)
        path(d, 14, 1, 22, 2)
    if L >= 3:                                                    # command centre
        building(d, 23, 14, 35, 22, nf=2, roof="flat", doors=(("north", 29), ("west", 18)), kinds=["office", "office"])
        for x in range(24, 35, 3):
            d.set(x, 1, 12, "moss_block")
            d.set(x, 2, 12, "azalea")
        bench(d, 26, 12, "north", 2)
        bench(d, 31, 12, "north", 2)
    if L >= 4:                                                    # barracks block
        building(d, 2, 20, 15, 29, nf=2 if L == 4 else 3, roof="flat", doors=(("north", 9), ("east", 24)),
                 kinds=["lounge", "bunks", "bunks"])
        path(d, 9, 17, 9, 19)
        for z in range(31, 35):
            d.set(4, 1, z, "moss_block")
            d.set(4, 2, z, "flowering_azalea" if z % 2 else "azalea")
    if L >= 5:                                                    # training hall with a roof court
        building(d, 18, 25, 40, 34, nf=2, roof="flat", doors=(("north", 23), ("north", 35), ("west", 30)),
                 kinds=["gym", "mess"])
        for x in range(38, 42):
            for z in range(14, 23):
                if (x + z) % 4 == 0:
                    d.set(x, 1, z, "moss_block")
                    d.set(x, 2, z, "azalea")
    return d


@design("guardtower")
def guardtower(pack, rel, L):
    return tidy({"Hearthwood": gt_hearthwood, "Cascadia": gt_cascadia, "Neoterra": gt_neoterra}[pack](rel, L))


# ================================================================================================ ARCHERY
"""
Archery
  Hearthwood  Village butts: brick-and-timber longhouse on the street (fletcher's shop + mess below, bunk room
              under the gable above), a covered shooting gallery on its back wall (L2+) and a hedged grass range
              with gravel lanes running to hay-bale butts and an earth berm.
  Cascadia    Hunting lodge: long log lodge with bunk beds on the west, a shooting shed with a shed roof at the
              head of a fenced range on the east, targets in front of a stacked-log backstop.
  Neoterra    Indoor archery centre: two-storey glazed clubhouse on the street (lobby/workshop, dorm above,
              roof terrace L4+) in front of a long white range hall with skylights, glass lane dividers and a
              lit black backstop.
"""
TARGETS = {1: 3, 2: 5, 3: 6, 4: 7, 5: 9}


def lane_order(xs):
    c = sum(xs) / len(xs)
    return sorted(xs, key=lambda x: (abs(x - c), x))


def place_beds(d, slots, n, color=None):
    """slots: list of (x, y, z, facing); places the first n."""
    for x, y, z, f in slots[:n]:
        d.bed(x, y, z, f, color)


def ar_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (44, 32, 34))
    X2 = {1: 13, 2: 13, 3: 17, 4: 21, 5: 23}[L]
    x1, z1, z2 = 3, 3, 9
    d.box(x1, 2, z1, X2, 5, z2, "bricks", floor="oak_planks")
    for x in range(x1, X2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, X2) or z in (z1, z2):
                d.set(x, 2, z, "stone_bricks")
    d.fill(x1, 6, z1, X2, 6, z2, "dark_oak_planks")
    hw_frame(d, x1, z1, X2, z2, 7, 10)
    soft(d, d.gable, x1, z1, X2, z2, 11, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite", 1)
    door = 7
    d.door(door, 2, z1, "south", "dark_oak")
    for x in range(x1 + 2, X2 - 1, 3):
        if abs(x - door) > 1:
            d.window(x, 3, z1, x, 4, z1)
    for x in range(x1 + 1, X2, 2):
        if x % 4 == 1:
            d.window(x, 8, z1, x, 9, z1)
            d.window(x, 8, z2, x, 9, z2)
    d.window(x1, 3, 6, x1, 4, 6)
    d.window(X2, 3, 6, X2, 4, 6)
    d.window(x1, 8, 6, x1, 9, 6)
    d.window(X2, 8, 6, X2, 9, 6)
    d.door(10, 2, z2, "north", "dark_oak")
    for x in (12, 13) if X2 > 13 else ():
        pass
    d.sign(door + 2, 5, z1 - 1, "east", ["The Butts", "Bowyers &", "Fletchers"], "dark_oak", hanging=True)
    d.set(door + 3, 5, z1 - 1, "dark_oak_planks")
    # ground floor: fletcher's shop and mess
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(X2 - 1, 2, z1 + 1, "furnace", "west")
    if L >= 3:
        d.item(X2 - 2, 2, z1 + 1, "fletching_table")
        d.set(X2 - 3, 2, z1 + 1, "crafting_table")
    else:
        d.set(X2 - 2, 2, z1 + 1, "crafting_table")
    weapon_rack(d, X2 - 1, z1 + 3, X2 - 1, z1 + 4, 2, "dark_oak", "west")
    d.keg(X2 - 1, 2, z2 - 1, "west")
    d.set(X2 - 1, 3, z2 - 1, "decorated_pot[cracked=false,facing=west,waterlogged=false]")
    d.dining(8, 2, 6, 2 if L < 3 else 4, "x", "dark_oak", ("n", "s"), sit=False)
    d.banner(x1 + 1, 4, 6, "east", "green")
    for x in range(x1 + 3, X2 - 1, 4):
        d.lamp(x, 5, 6)
    # stair up along the back wall
    flight(d, x1 + 1, 2, z2 - 1, "east", 4, "dark_oak", "dark_oak_planks")
    for x in range(x1 + 2, x1 + 5):
        d.set(x, 7, z2 - 2, "dark_oak_fence")
    # bunk room
    slots = [(x, 7, z1 + 1, "north") for x in range(x1 + 2, X2, 2)] + \
            [(x, 7, z2 - 1, "south") for x in range(x1 + 6, X2, 2)]
    place_beds(d, slots, d.req["beds"])
    for x, y, z, f in slots[:d.req["beds"]]:
        if d.air(x + 1, 7, z) and f == "north":
            d.set(x + 1, 7, z, "chest[facing=south,type=single,waterlogged=false]")
    d.rug(x1 + 5, 6, X2 - 2, 6, 7, ("green_carpet",), "plain")
    for x in range(x1 + 2, X2, 4):
        d.lamp(x, 10, 6)
    # range
    rz1, rz2 = 10, 28
    d.fill(2, 1, rz1, 24, 1, rz2 + 2, "grass_block[snowy=false]")
    xs = list(range(4, 21, 2))
    for z in range(rz1, rz2 + 1):
        for y in (2, 3):
            d.set(2, y, z, "oak_leaves[distance=7,persistent=true,waterlogged=false]")
            d.set(24, y, z, "oak_leaves[distance=7,persistent=true,waterlogged=false]")
    for x in xs:
        for z in range(13, rz2):
            d.set(x, 1, z, "gravel")
    order = lane_order(xs)
    for i, x in enumerate(order):
        d.set(x, 2, rz2, "hay_block[axis=y]")
        if i < TARGETS[L]:
            d.yard_item(x, 3, rz2, "target")
        else:
            d.set(x, 3, rz2, "hay_block[axis=x]")
    for x in range(3, 24):                                        # earth berm behind the butts
        d.set(x, 2, rz2 + 1, "dirt")
        d.set(x, 3, rz2 + 1, "grass_block[snowy=false]")
        d.set(x, 2, rz2 + 2, "grass_block[snowy=false]")
        if x not in xs:
            d.set(x, 2, rz2, "grass_block[snowy=false]")
            d.set(x, 3, rz2, "short_grass")
    d.fill(3, 1, rz1, 23, 1, 12, "gravel")
    for i, x in enumerate(order[:L]):
        d.spot(x, 2, 12, "work")
    if L >= 2:                                                    # covered shooting gallery
        gx2 = max(X2, 15)
        for x in range(x1, gx2 + 1):
            d.set(x, 5, 13, ST("deepslate_tile", "south"))
            for z in (10, 11, 12):
                d.set(x, 5, z, SL("deepslate_tile"))
        for x in range(x1, gx2 + 1, 4):
            for y in range(2, 5):
                d.set(x if x not in xs else x + 1, y, 12, LOG("stripped_dark_oak_log"))
        d.set(x1 + 2, 2, 10, "dark_oak_slab[type=bottom,waterlogged=false]") if False else None
    # quiver barrels and a bench at the line
    d.keg(23, 2, 11, "north")
    d.set(23, 3, 11, "hay_block[axis=y]") if False else None
    for x, z in ((2, rz1 - 1), (24, rz1 - 1)):
        pass
    d.set(22, 2, 10, "dark_oak_fence")
    d.set(22, 3, 10, LANT_S)
    if L >= 4:                                                    # spectators' benches by the hedge
        for z in range(15, 26, 4):
            d.chair(23, 2, z, "east", "dark_oak", sit=False)
            d.chair(23, 2, z + 1, "east", "dark_oak", sit=False)
    # ---- growth: the bowyers' guild yard east of the range
    if L >= 2:                                                    # bowyer's workshop (L3: loft store above)
        building(d, 27, 3, 35, 9, nf=1 if L == 2 else 2, axis="x", doors=(("north", 31), ("west", 6)),
                 chimney=(31, 10), kinds=["workshop", "store"])
        d.sign(29, 4, 2, "north", ["Bows &", "Arrows"], "dark_oak")
        for x in range(28, 35):                                   # striped awning over the shop window
            d.set(x, 5, 2, "red_wool" if x % 2 else "white_wool")
        lamp_post(d, 26, 1)
        cart(d, 37, 2, "x")
        flowerbed(d, 28, 0, 30, 1)
        flowerbed(d, 32, 0, 34, 1)
    if L >= 3:                                                    # timber store / seasoning shed for staves
        building(d, 27, 12, 35, 18, nf=1, axis="z", doors=(("north", 31),), kinds=["store"])
        for z in range(13, 18):                                   # stacked staves under the eaves
            d.set(37, 2, z, LOG("stripped_oak_log", "z"))
            d.set(37, 3, z, LOG("oak_log", "z") if z % 2 else LOG("birch_log", "z"))
        path(d, 25, 10, 42, 11)
    if L >= 4:                                                    # guild hall with mess and archers' quarters
        building(d, 27, 21, 42, 29, nf=2, axis="x", doors=(("north", 34), ("west", 25)), chimney=(43, 25),
                 kinds=["mess", "bunks"])
        bench(d, 28, 20, "south", 3)
        bench(d, 38, 20, "south", 3)
    if L >= 5:                                                    # guildmaster's house and a fenced orchard
        building(d, 37, 3, 43, 18, nf=4, axis="z", doors=(("west", 14),), kinds=["office", "lounge", "bunks", "store"])
        for x in (30, 34):                                        # a pair of market stalls on the forecourt
            for dx in (0, 2):
                for y in (2, 3, 4):
                    d.set(x + dx, y, 19, "oak_fence")
            for dx in range(3):
                d.set(x + dx, 5, 19, "red_wool" if dx % 2 == 0 else "white_wool")
                d.set(x + dx, 5, 18, "red_wool" if dx % 2 == 0 else "white_wool") if False else None
            d.set(x + 1, 2, 19, SL("oak", "top"))
            d.set(x + 1, 3, 19, "decorated_pot[cracked=false,facing=north,waterlogged=false]")
        for x in range(27, 43, 4):
            tree(d, x, 2, 32, "oak_log", "oak_leaves", 3, 1)
        for x in range(25, 44):
            if d.air(x, 2, 30):
                d.set(x, 2, 30, "oak_fence")
    return d


def ar_cascadia(rel, L):
    d = Design("Cascadia", rel, (46, 30, 40), paving="coarse_dirt")
    x1, x2, z1 = 2, 10, 3
    Z2 = {1: 13, 2: 13, 3: 15, 4: 15, 5: 17}[L]
    cs_walls(d, x1, z1, x2, Z2, 2, 6)
    d.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, Z2 - 1, "spruce_planks")
    ridge = cs_roof(d, x1, z1, x2, Z2, 7, "z")
    for x in range(x1 + 1, x2):                                   # board-and-batten front gable
        for y in range(7, ridge):
            if d.get(x, y, z1) == "minecraft:spruce_planks" and x % 2 == 0:
                d.set(x, y, z1, LOG("stripped_spruce_log"))
    d.door(6, 2, z1, "south", "spruce")
    d.window(4, 3, z1, 4, 5, z1)
    d.window(8, 3, z1, 8, 5, z1)
    d.window(6, 8, z1, 6, 9, z1)
    for z in range(z1 + 3, Z2, 3):
        d.window(x1, 3, z, x1, 4, z)
    d.door(x2, 2, z1 + 3, "east", "spruce")
    d.window(x2, 3, z1 + 1, x2, 4, z1 + 1)
    cs_trim(d, x1, z1, x2, Z2, 2, 6)
    d.set(5, 4, z1 - 1, "wall_torch[facing=north]") if False else None
    # elk antlers over the door: dead bushes on a bracket
    d.set(6, 5, z1 - 1, "spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    d.sign(6, 4, z1 - 1, "north", ["HUNTERS'", "LODGE"], "spruce")
    # stone chimney at the back
    d.hearth(6, 2, Z2 - 1, "north", 7, "cobblestone", "campfire")
    for y in range(1, ridge + 2):
        d.set(6, y, Z2, "mossy_cobblestone" if y % 3 == 0 else "cobblestone")
    # front room: workshop
    d.hut(x1 + 2, 2, z1 + 1)
    d.item(x1 + 1, 2, z1 + 3, "furnace", "east")
    if L >= 3:
        d.item(x1 + 1, 2, z1 + 4, "fletching_table")
    else:
        d.set(x1 + 1, 2, z1 + 4, "crafting_table")
    d.set(x2 - 1, 2, z1 + 1, "spruce_trapdoor[facing=west,half=top,open=false,powered=false,waterlogged=false]") if False else None
    weapon_rack(d, x2 - 1, z1 + 1, x2 - 1, z1 + 1, 2, "spruce", "west")
    d.table(6, 2, z1 + 3, "spruce")
    d.chair(5, 2, z1 + 3, "west", "spruce", sit=False)
    d.chair(7, 2, z1 + 3, "east", "spruce", sit=False)
    d.set(x1 + 1, 2, z1 + 5, "barrel[facing=up,open=false]")
    d.lamp(6, 6, z1 + 3)
    d.rug(4, z1 + 2, 8, z1 + 4, 2, ("brown_carpet", "green_carpet"))
    # bunk room: bunks (bed - slab - bed) along both walls
    zs = list(range(z1 + 8, Z2 - 1, 2))
    slots = []
    for z in zs:
        slots.append((x1 + 1, z, "west"))
    for z in zs:
        slots.append((x2 - 1, z, "east"))
    need = d.req["beds"]
    i = 0
    for x, z, f in slots:
        if i >= need:
            break
        d.bed(x, 2, z, f)
        i += 1
        if i < need:
            fx = x + (1 if f == "west" else -1)
            d.set(x, 3, z, SL("spruce", "top"))
            d.set(fx, 3, z, SL("spruce", "top"))
            d.bed(x, 4, z, f)
            i += 1
    for z in range(z1 + 7, Z2, 4):
        d.lamp(6, 6, z)
    d.fill(x1 + 1, 7, z1 + 1, x2 - 1, 7, Z2 - 1, "spruce_planks")
    # covered porch along the range side
    for z in range(z1, z1 + 6):
        d.set(x2 + 1, 1, z, "spruce_planks")
        d.set(x2 + 1, 5, z, SL("spruce"))
    # range on the east
    rx1, rx2 = 12, 30
    xs = list(range(13, 30, 2))
    for x in range(rx1, rx2 + 1):
        for z in range(1, 26):
            d.set(x, 1, z, "podzol" if (x * 3 + z) % 5 == 0 else "grass_block[snowy=false]")
    for x in xs:
        for z in range(7, 23):
            d.set(x, 1, z, "coarse_dirt")
    for z in range(1, 26):
        for x in (rx1, rx2):
            d.set(x, 2, z, "spruce_fence" if z % 4 else LOG("spruce_log"))
    d.set(rx1, 2, z1 + 3, AIR)
    d.set(x2 + 1, 2, z1 + 3, AIR) if False else None
    # shooting shed (north)
    for x in range(rx1 + 1, rx2):
        d.set(x, 1, 3, "spruce_planks")
        for z in (2, 3, 4, 5):
            d.set(x, 1, z, "spruce_planks")
        d.set(x, 6, 2, ST("spruce", "south"))
        d.set(x, 5, 6, ST("spruce", "north"))
        for z in (3, 4, 5):
            d.set(x, 6 if z < 4 else 5, z, SL("spruce", "bottom") if z >= 4 else SL("spruce", "bottom"))
    for x in range(rx1 + 1, rx2):
        d.set(x, 2, 2, "spruce_fence" if x % 6 else LOG("spruce_log"))
        for y in (3, 4, 5):
            if x % 6 == 0:
                d.set(x, y, 2, LOG("spruce_log"))
    for x in range(rx1 + 2, rx2, 6):
        for y in range(2, 5):
            d.set(x, y, 6, LOG("spruce_log"))
    order = lane_order(xs)
    for x in order[:L]:
        d.spot(x, 2, 5, "work")
    d.keg(rx2 - 1, 2, 3, "north")
    d.set(rx2 - 1, 3, 3, LANT_S)
    # log-crib backstop with targets
    for x in range(rx1 + 1, rx2):
        for y in (2, 3, 4):
            d.set(x, y, 24, LOG("spruce_log" if y != 3 else "stripped_spruce_log", "x"))
        d.set(x, 5, 24, SL("spruce"))
    for i, x in enumerate(order):
        d.set(x, 2, 23, "hay_block[axis=y]")
        if i < TARGETS[L]:
            d.yard_item(x, 3, 23, "target")
    for x in range(rx1 + 1, rx2):
        if x not in xs:
            d.set(x, 2, 23, "fern")
    if L >= 4:                                                   # skinning rack and stump seats by the lodge
        for z in (20, 22):
            d.set(4, 2, z, LOG("spruce_log"))
            d.set(4, 3, z, SL("spruce"))
        d.set(7, 2, 21, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        d.chair(7, 2, 20, "north", "spruce", sit=False) if False else None
        for x, z in ((6, 21), (8, 21), (7, 22)):
            d.set(x, 2, z, LOG("stripped_spruce_log"))
    # ---- growth: a hunting camp round the range
    if L >= 2:                                                    # outfitter's cabin (L3: loft with bunks)
        building(d, 33, 3, 42, 10, nf=1 if L == 2 else 2, axis="x", doors=(("north", 37), ("west", 7)),
                 chimney=(43, 7), kinds=["workshop", "bunks"])
        for x in range(33, 43):                                   # porch
            d.set(x, 1, 2, "spruce_planks")
            d.set(x, 1, 1, "spruce_planks")
        for x in (33, 42):
            for y in (2, 3, 4):
                d.set(x, y, 1, LOG("spruce_log"))
        for x in range(32, 44):
            d.set(x, 5, 1, SL("spruce"))
            d.set(x, 5, 2, SL("spruce"))
        d.sign(39, 4, 0, "north", ["OUTFITTER", "bows-traps"], "spruce")
        bench(d, 34, 2, "south", 2)
        d.keg(41, 2, 2, "north")
    if L >= 3:                                                    # smokehouse and game larder
        building(d, 33, 14, 40, 20, nf=1, axis="z", doors=(("north", 36),), chimney=(41, 17), kinds=["store"])
        for z in range(15, 20):
            d.set(43, 2, z, LOG("spruce_log", "z") if z % 2 else LOG("birch_log", "z"))
            d.set(43, 3, z, LOG("oak_log", "z"))
        cart(d, 33, 12, "x")
    if L >= 4:                                                    # lodge hall: mess below, trophy room above
        building(d, 2, 28, 17, 37, nf=2, axis="x", doors=(("north", 9), ("east", 33)), chimney=(1, 32),
                 kinds=["kitchen", "lounge"])
        for x in range(3, 17):
            d.set(x, 1, 27, "spruce_planks")
            d.set(x, 1, 26, "spruce_planks")
            d.set(x, 5, 26, ST("spruce", "north"))
            d.set(x, 5, 27, SL("spruce", "top"))
        for x in (3, 8, 12, 16):
            for y in (2, 3, 4):
                d.set(x, y, 26, LOG("spruce_log"))
        lamp_post(d, 19, 27)
    if L >= 5:                                                    # guest cabins along the creek path
        building(d, 21, 29, 29, 37, nf=2, axis="z", doors=(("north", 25),), kinds=["bunks", "bunks"])
        building(d, 33, 24, 43, 32, nf=2, axis="x", doors=(("north", 38), ("west", 28)), chimney=(44, 28),
                 kinds=["lounge", "bunks"])
        for x in range(18, 45):
            d.set(x, 1, 38, "coarse_dirt")
        tree(d, 31, 2, 36, "spruce_log", "spruce_leaves", 7, 2, cone=True)
        tree(d, 44, 2, 36, "spruce_log", "spruce_leaves", 6, 2, cone=True)
    return d


def ar_neoterra(rel, L):
    d = Design("Neoterra", rel, (44, 26, 45), paving="smooth_stone")
    x1, x2, z1, z2 = 3, 21, 2, 9
    # clubhouse
    nt_walls(d, x1, z1, x2, z2, 2, 6)
    d.fill(x1, 1, z1, x2, 1, z2, "polished_diorite")
    d.fill(x1, 7, z1, x2, 7, z2, "light_gray_concrete")
    nt_walls(d, x1, z1, x2, z2, 8, 11)
    d.flat(x1, z1, x2, z2, 12, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
    for x in range(x1, x2 + 1):
        d.set(x, 7, z1, "cyan_terracotta")
    for x in range(x1 + 1, x2):
        if x % 4 != 3:
            d.window(x, 2, z1, x, 5, z1, "glass_pane")
            d.window(x, 8, z1, x, 10, z1, "light_gray_stained_glass_pane")
    d.double_door(11, 2, z1, "x", "south", "birch")
    d.window(11, 5, z1, 12, 6, z1, "glass_pane")
    for x in range(10, 15):
        d.set(x, 6, z1 - 1, SL("smooth_quartz", "top"))
    d.sign(x1 + 4, 6, z1 - 1, "north", ["", "ARCHERY", "CENTRE"], "birch", glow=True, color="cyan")
    for z in range(z1 + 2, z2 - 1, 2):
        d.window(x1, 3, z, x1, 5, z)
        d.window(x2, 9, z, x2, 10, z)
    # lobby / workshop
    d.hut(x1 + 1, 2, z1 + 1)
    for x in range(14, 19):                                       # reception desk
        d.set(x, 2, z1 + 3, "smooth_quartz")
    d.chair(16, 2, z1 + 4, "south", "birch", sit=False) if False else None
    d.item(x2 - 1, 2, z1 + 1, "furnace", "west")
    if L >= 3:
        d.item(x2 - 1, 2, z1 + 2, "fletching_table")
    else:
        d.set(x2 - 1, 2, z1 + 2, "crafting_table")
    weapon_rack(d, x2 - 1, z1 + 4, x2 - 1, z1 + 5, 2, "birch", "west")
    for x in range(x1 + 3, x1 + 6):                               # lounge
        d.chair(x, 2, z1 + 1, "north", "birch", sit=False)
    d.set(x1 + 4, 2, z1 + 2, SL("smooth_quartz", "top"))
    d.plant(x1 + 6, 2, z1 + 1, "potted_bamboo")
    for x in range(x1 + 2, x2, 4):
        d.set(x, 6, 5, "sea_lantern")
    flight(d, x1 + 1, 2, z2 - 1, "east", 5, "smooth_quartz", "white_concrete")
    for x in range(x1 + 3, x1 + 6):
        d.set(x, 8, z2 - 2, "light_gray_stained_glass_pane")
    # dorm
    slots = [(x, 8, z1 + 1, "north") for x in range(x1 + 1, x2, 2)] + \
            [(x, 8, z2 - 1, "south") for x in range(x1 + 7, x2, 2)]
    place_beds(d, slots, d.req["beds"], "cyan")
    d.rug(x1 + 1, 5, x2 - 1, 6, 8, ("light_gray_carpet",), "plain")
    for x in range(x1 + 2, x2, 4):
        d.set(x, 11, 5, "sea_lantern")
    # range: open-air with glass screens (L1-2), enclosed hall with skylights from L3
    hz2 = 30
    if L >= 3:
        nt_walls(d, x1, z2, x2, hz2, 2, 7)
        for x in range(x1, x2 + 1):
            d.set(x, 7, z2, "light_gray_concrete")
        d.flat(x1, z2 + 1, x2, hz2, 8, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
        for z in range(z2 + 3, hz2 - 1, 4):
            for x in range(x1 + 2, x2 - 1):
                d.set(x, 8, z, "glass")
        for z in range(z2 + 2, hz2 - 1, 2):
            d.window(x1, 5, z, x1, 6, z, "glass_pane")
            d.window(x2, 5, z, x2, 6, z, "glass_pane")
        for z in range(z2 + 1, hz2 + 1):                          # cyan band and fins along the hall
            for x in (x1, x2):
                d.set(x, 7, z, "cyan_terracotta")
                if z % 4 == 0:
                    for y in range(2, 5):
                        d.set(x, y, z, "light_gray_concrete")
        for x in range(x1, x2 + 1):
            d.set(x, 7, hz2, "cyan_terracotta")
        d.sign(x2 + 1, 4, 14, "east", ["", "ARCHERY", "RANGE"], "birch", glow=True, color="cyan")
    else:
        for z in range(z2 + 1, hz2 + 1):
            for x in (x1, x2):
                d.set(x, 2, z, "white_concrete")
                d.set(x, 3, z, "light_gray_stained_glass_pane")
        for x in range(x1, x2 + 1):
            d.set(x, 2, hz2, "white_concrete")
    d.double_door(13, 2, z2, "x", "north", "birch")
    d.fill(x1 + 1, 1, z2 + 1, x2 - 1, 1, hz2 - 1, "smooth_stone")
    d.fill(x1 + 1, 1, z2 + 4, x2 - 1, 1, z2 + 4, "cyan_concrete")                 # shooting line
    xs = list(range(4, 21, 2))
    order = lane_order(xs)
    for x in xs:
        for z in range(z2 + 5, hz2 - 1):
            d.set(x, 1, z, "light_gray_concrete")
    for x in range(5, 20, 2):
        for z in range(z2 + 5, z2 + 10):
            d.set(x, 2, z, "light_gray_stained_glass_pane")
    for x in range(x1 + 1, x2):                                   # backstop
        for y in range(2, 7):
            d.set(x, y, hz2 - 1, "black_concrete")
        d.set(x, 7, hz2 - 1, "sea_lantern" if x % 2 == 0 else "black_concrete")
    for i, x in enumerate(order):
        d.set(x, 2, hz2 - 2, "white_concrete")
        if i < TARGETS[L]:
            d.yard_item(x, 3, hz2 - 2, "target")
    for x in order[:L]:
        d.spot(x, 2, z2 + 3, "work")
    for x in (x1 + 1, x2 - 1):
        d.chair(x, 2, z2 + 2, "north", "birch", sit=False)
    if L >= 4:                                                    # roof terrace
        d.set(x2 - 1, 12, z2 - 1, AIR)
        ladder(d, x2 - 1, z2 - 1, 8, 12, "north")
        d.set(x2 - 1, 8, z2 - 1, "ladder[facing=north,waterlogged=false]")
        for x in range(x1 + 2, x2 - 2, 3):
            d.set(x, 13, z1 + 1, "azalea")
            d.set(x, 13, z2 - 2, "moss_carpet")
        for x in range(x1 + 3, x1 + 9, 2):
            d.chair(x, 13, z1 + 4, "south", "birch", sit=False)
        d.set(x1 + 10, 13, z1 + 4, "smooth_quartz_slab[type=top,waterlogged=false]")
    # ---- growth: an archery club campus east of the range
    if L >= 2:                                                    # pro shop / bowyer's workshop (L3: offices above)
        building(d, 25, 2, 37, 10, nf=2, roof="flat", doors=(("north", 28), ("west", 6)),
                 kinds=["workshop", "office"])
        d.sign(33, 5, 1, "north", ["", "PRO SHOP"], "birch", glow=True, color="cyan")
        for x in range(26, 37, 2):
            d.set(x, 6, 1, SL("smooth_quartz", "top"))
        lamp_post(d, 23, 1)
        lamp_post(d, 39, 1)
        path(d, 22, 1, 40, 1)
        for x in (40, 42):
            d.set(x, 1, 5, "moss_block")
            d.set(x, 2, 5, "azalea")
    if L >= 3:                                                    # cafe pavilion and terrace between shop and hall
        building(d, 32, 12, 40, 18, nf=1, roof="flat", doors=(("west", 15),), kinds=["kitchen"])
        for z in range(13, 18, 2):
            d.table(27, 2, z, "birch", "slab", "smooth_quartz_slab")
            d.chair(26, 2, z, "west", "birch", sit=False)
            d.chair(28, 2, z, "east", "birch", sit=False)
        for x in range(25, 31):
            d.set(x, 1, 12, "moss_block")
            d.set(x, 2, 12, "azalea" if x % 2 else "flowering_azalea")
    if L >= 4:                                                    # residence for the archers
        building(d, 25, 20, 40, 30, nf=3 if L == 4 else 4, roof="flat", doors=(("north", 30), ("west", 25)),
                 kinds=["lounge", "bunks", "bunks", "lounge"])
        path(d, 22, 25, 24, 25)
    if L >= 5:                                                    # field range with clubhouse and covered stand
        fx1, fz1, fx2, fz2 = 16, 33, 42, 44
        for x in range(fx1, fx2 + 1):
            for z in range(fz1, fz2 + 1):
                d.set(x, 1, z, "grass_block[snowy=false]")
                if x == fx2 or z == fz2:
                    d.set(x, 2, z, "birch_leaves[distance=1,persistent=true,waterlogged=false]")
        for x in range(fx1 + 2, fx2 - 1, 3):
            d.set(x, 2, fz2 - 1, "hay_block[axis=y]")
            d.set(x, 3, fz2 - 1, "target[power=0]")
            for z in range(fz1 + 4, fz2 - 1):
                d.set(x, 1, z, "light_gray_concrete")
        for x in range(fx1, fx2):                                 # covered stand
            d.set(x, 2, fz1, "white_concrete")
            d.chair(x, 3, fz1, "north", "birch", sit=False)
            d.chair(x, 2, fz1 + 1, "north", "birch", sit=False)
            for z in range(fz1 - 1, fz1 + 3):
                d.set(x, 7, z, SL("smooth_quartz"))
        for x in range(fx1, fx2, 6):
            for y in range(2, 7):
                d.set(x, y, fz1 - 1, "light_gray_concrete")
        building(d, 2, 33, 14, 44, nf=4, roof="flat", doors=(("north", 8), ("east", 38)),
                 kinds=["mess", "lounge", "office", "bunks"])

    return d


@design("archery")
def archery(pack, rel, L):
    return tidy({"Hearthwood": ar_hearthwood, "Cascadia": ar_cascadia, "Neoterra": ar_neoterra}[pack](rel, L))


# ================================================================================================ COMBAT ACADEMY
"""
Combat academy
  Hearthwood  Fencing school & tiltyard: gable-fronted brick-and-timber drill hall on the west (armoury and
              forge below, barracks under the roof), a fenced sand ring with pells and dummies on the east, and
              (L2+) a three-tier grandstand under a red-and-white striped canopy on the south side.
  Cascadia    Fight barn: a big log barn with a dirt sparring ring fenced in the middle, two-tier log bleachers
              along both long walls (L2+), a bunk loft over the front armoury and (L3+) a forge lean-to.
  Neoterra    Rooftop arena: a low glazed training centre (lobby, gym with dummies, dorm) whose roof is an
              open-air court with ring markings, floodlight masts, a stair kiosk and (L2+) tiered stands under a
              cantilevered canopy.
"""


def ca_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (46, 34, 39))
    x1, x2, z1 = 2, 10, 2
    Z2 = {1: 12, 2: 14, 3: 16, 4: 18, 5: 20}[L]
    d.box(x1, 2, z1, x2, 5, Z2, "bricks", floor="spruce_planks")
    for x in range(x1, x2 + 1):
        for z in range(z1, Z2 + 1):
            if x in (x1, x2) or z in (z1, Z2):
                d.set(x, 2, z, "stone_bricks")
    d.fill(x1, 6, z1, x2, 6, Z2, "dark_oak_planks")
    hw_frame(d, x1, z1, x2, Z2, 7, 10)
    soft(d, d.gable, x1, z1, x2, Z2, 11, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite", 1)
    for y in range(11, 15):
        d.set(6, y, z1, LOG("stripped_dark_oak_log"))
    # big arched double door and crossed-sword sign
    d.double_door(5, 2, z1, "x", "south", "dark_oak")
    d.set(5, 4, z1, ST("stone_brick", "west", "top"))
    d.set(6, 4, z1, ST("stone_brick", "east", "top"))
    d.banner(4, 4, z1 - 1, "north", "red")
    d.banner(7, 4, z1 - 1, "north", "red")
    d.sign(6, 5, z1 - 1, "north", ["Academy of", "Arms"], "dark_oak")
    d.window(3, 3, z1, 3, 4, z1)
    d.window(9, 3, z1, 9, 4, z1)
    for x in (4, 8):
        d.window(x, 8, z1, x, 9, z1)
    d.window(6, 12, z1, 6, 12, z1) if False else None
    for z in range(z1 + 2, Z2 - 1, 3):
        d.window(x1, 3, z, x1, 4, z)
        d.window(x1, 8, z, x1, 9, z)
        d.window(x2, 8, z, x2, 9, z)
    d.door(x2, 2, z1 + 3, "east", "dark_oak")
    # armoury / forge
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x1 + 1, 2, z1 + 3, "furnace", "east")
    d.item(x1 + 1, 2, z1 + 4, "barrel")
    if L >= 3:
        d.item(x1 + 1, 2, z1 + 6, "anvil", "south")
        d.item(x1 + 1, 2, z1 + 7, "grindstone", "east")
    d.set(x1 + 1, 2, z1 + 5, "water_cauldron[level=3]")
    weapon_rack(d, x2 - 1, z1 + 1, x2 - 1, z1 + 2, 2, "dark_oak", "west")
    d.banner(x2 - 1, 4, z1 + 5, "west", "red")
    dummy(d, 7, 2, z1 + 6, "west")
    d.lamp(6, 5, z1 + 3)
    d.lamp(6, 5, Z2 - 3)
    # stairs up the middle aisle (rising south)
    sz = Z2 - 5
    flight(d, 6, 2, sz, "south", 4, "dark_oak", "dark_oak_planks")
    for z in range(sz, sz + 3):
        d.set(5, 7, z, "dark_oak_fence")
        d.set(7, 7, z, "dark_oak_fence")
    # barracks under the roof
    slots = []
    for z in range(z1 + 1, Z2, 2):
        slots += [(x1 + 1, 7, z, "west"), (x2 - 1, 7, z, "east")]
    place_beds(d, slots, d.req["beds"])
    for x, y, z, f in slots[:d.req["beds"]]:
        if d.air(x, 7, z + 1) and z + 1 < Z2:
            d.set(x, 7, z + 1, "chest[facing=%s,type=single,waterlogged=false]" % ("east" if f == "west" else "west"))
    for z in range(z1 + 2, Z2, 4):
        d.lamp(6, 12, z) if d.air(6, 12, z) else None
    # sand ring
    rx1, rz1, rx2, rz2 = 13, 3, 27, 18
    d.fill(rx1, 1, rz1, rx2, 1, rz2, "sand")
    for x in range(rx1, rx2 + 1):
        for z in range(rz1, rz2 + 1):
            if x in (rx1, rx2) or z in (rz1, rz2):
                d.set(x, 1, z, "stone_bricks")
                d.set(x, 2, z, "dark_oak_fence" if (x + z) % 5 else LOG("stripped_dark_oak_log"))
    d.set(rx1, 2, 5, "dark_oak_fence_gate[facing=east,in_wall=false,open=false,powered=false]")
    d.fill(x2 + 1, 1, 5, rx1, 1, 5, "gravel")
    d.set(20, 2, rz1, "dark_oak_fence_gate[facing=north,in_wall=false,open=false,powered=false]")
    d.fill(20, 1, 0, 20, 1, rz1 - 1, "gravel")
    for x in (16, 20, 24):
        dummy(d, x, 2, rz1 + 2, "south")
    for z in (8, 12):                                             # pells: posts to hack at
        d.set(rx2 - 2, 2, z, LOG("stripped_oak_log"))
        d.set(rx2 - 2, 3, z, LOG("stripped_oak_log"))
    d.set(rx2 - 1, 2, rz1 + 1, "hay_block[axis=y]")
    d.set(rx2 - 1, 3, rz1 + 1, "target[power=0]")
    weapon_rack(d, rx1 + 1, 9, rx1 + 1, 12, 2, "dark_oak", "east")
    d.rug(17, 9, 21, 13, 2, ("white_carpet", "red_carpet"))
    for x, z in ((rx1, rz1), (rx2, rz1), (rx1, rz2), (rx2, rz2)):
        d.set(x, 3, z, LANT_S)
    if L >= 2:                                                    # grandstand
        gx1, gx2 = 14, 26
        n = 0
        for x in range(gx1, gx2 + 1):
            for t, z in enumerate((20, 21, 22)):
                d.set(x, 1, z, "stone_bricks")
                for y in range(2, 2 + t):
                    d.set(x, y, z, "dark_oak_planks")
                if n < 32 and x not in (gx1, gx2):
                    d.chair(x, 2 + t, z, "south", "dark_oak")
                    n += 1
                else:
                    d.set(x, 2 + t, z, SL("dark_oak"))
        for x in range(gx1 - 1, gx2 + 2):
            for y in range(2, 6):
                d.set(x, y, 23, "bricks" if x in (gx1 - 1, gx2 + 1) else ("dark_oak_planks" if y < 4 else AIR))
        for x in (gx1 - 1, gx2 + 1, 20):
            for y in range(2, 8):
                d.set(x, y, 23, LOG("stripped_dark_oak_log"))
            for y in range(2, 7):
                d.set(x, y, 19, "dark_oak_fence" if x != 20 else AIR)
        for x in range(gx1 - 1, gx2 + 2):
            for z in range(19, 24):
                y = 7 if z >= 21 else 6
                d.set(x, y, z, "red_wool" if x % 2 else "white_wool")
            d.set(x, 6, 19, ST("dark_oak", "south", "top") if False else ("red_wool" if x % 2 else "white_wool"))
        for x in range(gx1, gx2 + 1, 3):
            d.banner(x, 5, 18, "north", "red" if x % 2 else "white") if d.air(x, 5, 18) else None
    if L >= 4:                                                    # quintain in the ring
        d.set(24, 2, 15, "dark_oak_fence")
        d.set(24, 3, 15, "dark_oak_fence")
        d.set(24, 4, 15, "dark_oak_fence")
        d.set(23, 4, 15, "dark_oak_fence")
        d.set(25, 4, 15, "dark_oak_fence")
        d.set(23, 3, 15, "white_banner") if False else None
        d.set(16, 2, 15, "hay_block[axis=y]")
        d.set(16, 3, 15, "target[power=0]")
    if L >= 5:
        for x in (rx1, rx2):
            for y in range(3, 7):
                d.set(x, y, rz1, LOG("stripped_dark_oak_log"))
            d.banner(x, 6, rz1 - 1, "north", "red")
    # ---- growth: a school of arms round the tiltyard
    if L >= 2:                                                    # stable for the tilting horses
        building(d, 31, 3, 40, 9, nf=1, axis="x", doors=(("north", 33), ("north", 38)), kinds=["store"])
        for x in range(31, 41):                                   # paddock
            for z in range(11, 16):
                if x in (31, 40) or z in (11, 15):
                    d.set(x, 2, z, "dark_oak_fence")
        d.set(35, 2, 11, "dark_oak_fence_gate[facing=north,in_wall=false,open=false,powered=false]")
        d.set(33, 2, 13, "hay_block[axis=y]")
        d.set(38, 2, 13, "water_cauldron[level=3]")
        lamp_post(d, 29, 1)
    if L >= 3:                                                    # armourer's forge with a loft
        building(d, 31, 18, 41, 24, nf=2, axis="z", doors=(("north", 36), ("west", 21)), chimney=(42, 21),
                 kinds=["workshop", "store"])
        d.set(30, 2, 18, "anvil[facing=north]")
        d.set(30, 2, 19, "water_cauldron[level=3]") if False else None
        d.sign(34, 4, 17, "north", ["Armourer"], "dark_oak")
    if L >= 4:                                                    # masters' house: library, office, rooms
        building(d, 2, 27, 16, 36, nf=2, axis="x", doors=(("north", 9), ("east", 31)), chimney=(17, 31),
                 kinds=["library", "office"])
        flowerbed(d, 3, 25, 6, 26)
        flowerbed(d, 12, 25, 15, 26)
        bench(d, 8, 25, "south", 2) if False else None
        lamp_post(d, 1, 25)
    if L >= 5:                                                    # great hall with a gatehouse tower
        building(d, 20, 28, 38, 37, nf=2, axis="x", doors=(("north", 29), ("west", 33)), chimney=(29, 38),
                 kinds=["mess", "bunks"])
        building(d, 39, 28, 45, 37, nf=4, roof="hip", ground="stone_bricks", doors=(("north", None),),
                 kinds=["armoury", "office", "bunks", "office"])
        for x in range(20, 39, 4):
            d.banner(x, 5, 27, "north", "red" if x % 8 else "white")
    return d


def ca_cascadia(rel, L):
    d = Design("Cascadia", rel, (46, 32, 45), paving="coarse_dirt")
    x1, x2, z1 = 3, 19, 4
    Z2 = 16 if L == 1 else 25
    cs_walls(d, x1, z1, x2, Z2, 2, 7)
    d.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, Z2 - 1, "spruce_planks")
    cs_roof(d, x1, z1, x2, Z2, 8, "z")
    for z in range(z1 + 4, Z2 - 1, 5):                            # stripped posts breaking up the long walls
        for x in (x1, x2):
            for y in range(3, 8):
                d.set(x, y, z, LOG("stripped_spruce_log"))
    for x in range(x1, x2 + 1):                                   # board-and-batten gables over the logs
        for y in range(8, 18):
            for z in (z1, Z2):
                if d.get(x, y, z) == "minecraft:spruce_planks" and x % 3 == 0:
                    d.set(x, y, z, LOG("stripped_spruce_log"))
    mid = 11
    d.double_door(mid - 1, 2, z1, "x", "south", "spruce")
    d.double_door(mid + 1, 2, z1, "x", "south", "spruce") if False else None
    for y in (2, 3):
        d.set(mid + 1, y, z1, AIR)
    d.set(mid + 1, 2, z1, "spruce_fence_gate[facing=north,in_wall=false,open=false,powered=false]")
    for x in range(mid - 2, mid + 3):
        d.set(x, 4, z1, LOG("stripped_spruce_log", "x"))
    d.window(mid - 4, 3, z1, mid - 4, 5, z1)
    d.window(mid + 4, 3, z1, mid + 4, 5, z1)
    d.window(mid - 1, 9, z1, mid + 1, 11, z1)                      # hay-loft window
    d.set(mid, 9, z1, LOG("stripped_spruce_log"))
    d.set(mid, 10, z1, LOG("stripped_spruce_log"))
    d.set(mid, 11, z1, LOG("stripped_spruce_log"))
    for x in range(mid - 2, mid + 3):
        d.set(x, 12, z1, LOG("stripped_spruce_log", "x"))
        d.set(x, 8, z1, LOG("stripped_spruce_log", "x"))
    d.set(mid, 13, z1 - 1, LOG("stripped_spruce_log", "z"))        # hoist beam
    d.set(mid, 12, z1 - 1, "chain[axis=y,waterlogged=false]") if d.air(mid, 12, z1 - 1) else None
    d.sign(mid, 6, z1 - 1, "north", ["FIGHT BARN", "est. 1902"], "spruce")
    for x in (mid - 3, mid + 3):
        d.set(x, 5, z1 - 1, LANT) if False else None
    d.set(mid - 3, 4, z1 - 1, "wall_torch[facing=north]")
    d.set(mid + 3, 4, z1 - 1, "wall_torch[facing=north]")
    for z in range(z1 + 2, Z2 - 2, 5):                            # grouped windows, three wide
        for x in (x1, x2):
            d.window(x, 4, z, x, 5, z + 2)
    cs_trim(d, x1, z1, x2, Z2, 2, 7)
    # lean-to woodshed porch along the west wall
    for z in range(z1 + 2, Z2 - 1):
        for x in (0, 1, 2):
            d.set(x, 1, z, "spruce_planks")
        d.set(0, 5, z, ST("deepslate_tile", "east"))
        d.set(1, 6, z, SL("deepslate_tile"))
        d.set(2, 6, z, SL("deepslate_tile"))
        d.set(0, 4, z, LOG("stripped_spruce_log", "z")) if (z - z1) % 4 else None
        if (z - z1 - 2) % 4 == 0 or z == Z2 - 2:
            for y in range(2, 5):
                d.set(0, y, z, LOG("spruce_log"))
        elif z > z1 + 6:
            d.set(0, 2, z, LOG("spruce_log", "z") if z % 2 else LOG("birch_log", "z"))
            d.set(0, 3, z, LOG("oak_log", "z") if z % 3 else LOG("spruce_log", "z"))
    d.door(x1, 2, z1 + 5, "west", "spruce")
    d.set(x1 - 1, 4, z1 + 5, LANT) if False else None
    d.set(1, 5, z1 + 5, LANT)
    d.chair(1, 2, z1 + 3, "west", "spruce", sit=False)
    d.keg(1, 2, z1 + 2, "north") if False else None
    # front: armoury, hut and gear
    d.hut(x1 + 1, 2, z1 + 1)
    d.item(x1 + 1, 2, z1 + 3, "furnace", "east")
    d.item(x1 + 1, 2, z1 + 4, "barrel")
    d.set(x1 + 1, 2, z1 + 2, "water_cauldron[level=3]")
    weapon_rack(d, x2 - 1, z1 + 1, x2 - 1, z1 + 4, 2, "spruce", "west")
    d.set(x2 - 2, 2, z1 + 1, "barrel[facing=north,open=false]")
    # bunk loft over the front (deck y6), ladder against the west wall
    d.fill(x1 + 1, 6, z1 + 1, x2 - 1, 6, z1 + 5, "spruce_planks")
    for x in range(x1 + 1, x2):
        d.set(x, 7, z1 + 6, "spruce_fence")
        d.set(x, 5, z1 + 6, ST("spruce", "north", "top")) if x % 2 else None
    ladder(d, x1 + 1, z1 + 6, 2, 7, "east")
    d.set(x1 + 1, 7, z1 + 6, "ladder[facing=east,waterlogged=false]")
    d.set(x1 + 2, 7, z1 + 6, AIR)
    slots = [(x, 7, z1 + 1, "north") for x in range(x1 + 2, x2, 2)] + \
            [(x, 7, z1 + 4, "south") for x in range(x1 + 4, x2, 2)]
    # head south at z1+4 means foot at z1+3: keep z1+5 walkway? use z1+5 heads south
    slots = [(x, 7, z1 + 1, "north") for x in range(x1 + 2, x2, 2)] + \
            [(x, 7, z1 + 5, "south") for x in range(x1 + 4, x2, 2)]
    place_beds(d, slots, d.req["beds"])
    for x in range(x1 + 3, x2, 4):
        d.lamp(x, 5, z1 + 3)
        if d.air(x, 11, z1 + 3):
            d.lamp(x, 11, z1 + 3)
    # sparring ring
    rx1, rx2 = 7, 15
    rz1, rz2 = z1 + 8, Z2 - 3
    for x in range(rx1, rx2 + 1):
        for z in range(rz1, rz2 + 1):
            d.set(x, 1, z, "coarse_dirt" if (x + z) % 3 else "dirt")
            if x in (rx1, rx2) or z in (rz1, rz2):
                d.set(x, 2, z, "spruce_fence" if (x, z) not in ((rx1, rz1), (rx2, rz1), (rx1, rz2), (rx2, rz2))
                      else LOG("spruce_log"))
    d.set(11, 2, rz1, "spruce_fence_gate[facing=north,in_wall=false,open=false,powered=false]")
    for x, z in ((rx1, rz1), (rx2, rz1), (rx1, rz2), (rx2, rz2)):
        d.set(x, 3, z, LANT_S)
    dummy(d, 9, 2, rz1 + 2, "south")
    dummy(d, 13, 2, rz1 + 2, "south")
    d.set(11, 2, rz2 - 1, "hay_block[axis=x]")
    d.set(10, 2, rz2 - 1, "hay_block[axis=x]")
    for z in range(rz1, rz2 + 1, 4):
        d.lamp(11, 7, z)
    if L >= 2:                                                    # bleachers along both walls
        n = 0
        for z in range(z1 + 9, z1 + 17):
            for x, xb, f in ((x1 + 2, x1 + 1, "west"), (x2 - 2, x2 - 1, "east")):
                d.chair(x, 2, z, f, "spruce")
                d.set(xb, 2, z, LOG("spruce_log", "z"))
                d.chair(xb, 3, z, f, "spruce")
                n += 2
        for z in (z1 + 8, z1 + 17):
            for x in (x1 + 1, x1 + 2, x2 - 2, x2 - 1):
                d.set(x, 2, z, LOG("stripped_spruce_log"))
    else:
        d.set(x2, 2, Z2 - 3, AIR)
    if L >= 3:                                                    # forge lean-to on the east wall
        fx1, fx2 = x2, x2 + 5
        fz1, fz2 = z1 + 2, z1 + 8
        for x in range(fx1 + 1, fx2 + 1):
            for z in range(fz1, fz2 + 1):
                d.set(x, 1, z, "cobblestone")
                d.set(x, 6 - (x - fx1) // 2, z, SL("dark_oak") if (x - fx1) % 2 == 0 else "dark_oak_planks")
        for x, z in ((fx2, fz1), (fx2, fz2)):
            for y in range(2, 4):
                d.set(x, y, z, LOG("spruce_log"))
        d.item(fx1 + 2, 2, fz1 + 2, "anvil", "south")
        d.item(fx1 + 2, 2, fz1 + 4, "grindstone", "east")
        d.set(fx2, 2, fz1 + 3, "cobblestone")
        d.set(fx2, 3, fz1 + 3, "cobblestone")
        d.set(fx2 - 1, 2, fz1 + 3, "campfire[facing=west,lit=true,signal_fire=false,waterlogged=false]")
        d.set(fx1 + 1, 2, fz2, "water_cauldron[level=3]")
        d.door(x2, 2, fz1 + 3, "east", "spruce")
    if L >= 4:                                                    # outdoor log-lifting yard
        for x in (22, 24):
            d.set(x, 2, 18, LOG("spruce_log", "z"))
            d.set(x, 2, 19, LOG("spruce_log", "z"))
        dummy(d, 23, 2, 22, "west")
        d.set(25, 2, 22, "hay_block[axis=y]")
        d.set(25, 3, 22, "target[power=0]")
    if L >= 5:
        for z in (z1 + 9, z1 + 13):
            d.banner(x1 + 1, 6, z, "east", "green")
            d.banner(x2 - 1, 6, z, "west", "green")
    # ---- growth: a logging-camp athletic club round the fight barn
    if L >= 2:                                                    # fighters' bunkhouse
        building(d, 23, 4, 32, 11, nf=1, axis="x", doors=(("north", 27), ("west", 8)), chimney=(33, 8),
                 kinds=["bunks"])
        for x in range(23, 33):
            d.set(x, 1, 3, "spruce_planks")
            d.set(x, 1, 2, "spruce_planks")
            d.set(x, 5, 2, SL("spruce", "top"))
            d.set(x, 5, 3, SL("spruce", "top"))
        for x in (23, 32):
            for y in (2, 3, 4):
                d.set(x, y, 2, LOG("spruce_log"))
        bench(d, 24, 3, "south", 2)
        lamp_post(d, 21, 1)
    if L >= 3:                                                    # cook shack and mess with a sauna loft
        building(d, 23, 14, 36, 21, nf=2, axis="z", doors=(("north", 28), ("west", 18)), chimney=(37, 18),
                 kinds=["kitchen", "lounge"])
        cart(d, 39, 14, "z")
    if L >= 4:                                                    # timbersports yard: chopping blocks, log toss
        for x in range(3, 20, 3):
            d.set(x, 2, 30, LOG("spruce_log"))
            d.set(x, 3, 30, LOG("stripped_spruce_log")) if x % 2 else None
        for x in range(2, 21):
            for z in (28, 34):
                d.set(x, 2, z, "spruce_fence")
        building(d, 23, 24, 41, 34, nf=2, axis="x", doors=(("north", 29), ("west", 29)), chimney=(42, 29),
                 kinds=["gym", "bunks"])
    if L >= 5:                                                    # trophy lodge and boathouse-style gym
        building(d, 2, 36, 20, 43, nf=2, axis="x", doors=(("north", 11), ("east", 40)), chimney=(1, 40),
                 kinds=["mess", "lounge"])
        building(d, 23, 36, 37, 43, nf=2, axis="x", doors=(("north", 30),), kinds=["gym", "office"])
        for z in range(3, 40, 6):
            tree(d, 43, 2, z, "dark_oak_log", "spruce_leaves", 7, 2, cone=True)
        for x in (8, 14):                                         # log gate arch to the timbersports yard
            for y in range(2, 7):
                d.set(x, y, 27, LOG("spruce_log"))
        for x in range(7, 16):
            d.set(x, 7, 27, LOG("stripped_spruce_log", "x"))
        d.sign(11, 6, 26, "north", ["TIMBER", "GAMES"], "spruce")
    return d


def ca_neoterra(rel, L):
    d = Design("Neoterra", rel, (47, 34, 47), paving="smooth_stone")
    x1, z1, x2, z2 = 2, 3, 20, 19
    nt_walls(d, x1, z1, x2, z2, 2, 6)
    d.fill(x1, 1, z1, x2, 1, z2, "polished_diorite")
    d.fill(x1, 7, z1, x2, 7, z2, "light_gray_concrete")
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, 7, z, "cyan_terracotta")
                d.set(x, 8, z, "light_gray_stained_glass_pane")
    for x in range(x1 + 1, x2):                                   # glazed street front
        if x % 3 != 2:
            d.window(x, 2, z1, x, 5, z1, "glass_pane")
    for z in range(z1 + 2, z2 - 1, 3):
        d.window(x1, 3, z, x1, 5, z)
        d.window(x2, 3, z, x2, 5, z)
    d.double_door(10, 2, z1, "x", "south", "birch")
    d.sign(13, 6, z1 - 1, "north", ["", "COMBAT", "ACADEMY"], "birch", glow=True, color="cyan")
    # court markings on the roof
    for x in range(x1 + 1, x2):
        for z in range(z1 + 1, z2):
            r = ((x - 11) ** 2 + (z - 13) ** 2) ** 0.5
            if 4.5 <= r < 5.5:
                d.set(x, 7, z, "cyan_concrete")
            elif r < 1:
                d.set(x, 7, z, "white_concrete")
    # floodlight masts
    for x, z in ((x1 + 1, z2 - 1), (x2 - 1, z2 - 1), (x2 - 1, z1 + 1)):
        for y in range(8, 12):
            d.set(x, y, z, "iron_bars")
        d.set(x, 12, z, "sea_lantern")
        d.set(x, 13, z, "daylight_detector[inverted=false,power=0]")
    # ground floor: lobby / armoury (north), gym (west), dorm (east)
    d.hut(x1 + 1, 2, z1 + 1)
    for x in range(x1 + 4, x1 + 7):
        d.set(x, 2, z1 + 3, "smooth_quartz")
    d.item(x2 - 1, 2, z1 + 1, "furnace", "west")
    d.item(x2 - 1, 2, z1 + 2, "barrel")
    if L >= 3:
        d.item(x2 - 1, 2, z1 + 4, "anvil", "south")
        d.item(x2 - 2, 2, z1 + 4, "grindstone", "north")
    weapon_rack(d, x2 - 4, z1 + 1, x2 - 2, z1 + 1, 2, "birch", "south")
    for x in range(x1 + 1, x2):                                   # partition
        if x in (6, 7, 14, 15):
            continue
        d.set(x, 2, z1 + 5, "white_concrete")
        for y in (3, 4):
            d.set(x, y, z1 + 5, "light_gray_stained_glass_pane")
        d.set(x, 5, z1 + 5, "white_concrete")
        d.set(x, 6, z1 + 5, "white_concrete")
    for x in (6, 7, 14, 15):
        d.set(x, 4, z1 + 5, "white_concrete")
        d.set(x, 5, z1 + 5, "white_concrete")
        d.set(x, 6, z1 + 5, "white_concrete")
    for z in range(z1 + 6, z2):
        if z in (z1 + 8,):
            continue
        d.set(11, 2, z, "white_concrete")
        for y in (3, 4):
            d.set(11, y, z, "light_gray_stained_glass_pane")
        d.set(11, 5, z, "white_concrete")
        d.set(11, 6, z, "white_concrete")
    d.set(11, 4, z1 + 8, "white_concrete")
    # gym
    d.rug(x1 + 2, z1 + 7, 9, z2 - 1, 2, ("blue_carpet", "light_blue_carpet"))
    for z in (z1 + 9, z1 + 12):
        dummy(d, 5, 2, z, "east")
        d.set(9, 2, z, "iron_block")
        d.set(9, 3, z, "target[power=0]")
    # stair to the roof along the west wall (rising south)
    flight(d, x1 + 1, 2, z1 + 7, "south", 5, "smooth_quartz", "white_concrete")
    # kiosk over the stair on the roof
    kx1, kz1, kx2, kz2 = x1, z1 + 8, x1 + 3, z1 + 13
    for x in range(kx1, kx2 + 1):
        for z in range(kz1, kz2 + 1):
            if x in (kx1, kx2) or z in (kz1, kz2):
                for y in range(8, 11):
                    d.set(x, y, z, "white_concrete" if x == kx1 or y == 10 else "light_gray_stained_glass_pane")
    d.fill(kx1, 11, kz1, kx2, 11, kz2, "smooth_quartz_slab[type=bottom,waterlogged=false]")
    d.door(kx2, 8, kz2 - 1, "east", "birch")
    # dorm
    slots = []
    for z in range(z1 + 6, z2, 2):
        slots += [(x2 - 1, 2, z, "east"), (12, 2, z, "west")]
    place_beds(d, slots, d.req["beds"], "cyan")
    for x in range(x1 + 3, x2, 4):
        for z in (z1 + 2, z1 + 9, z1 + 13):
            d.set(x, 6, z, "sea_lantern")
    # roof furniture
    dummy(d, 8, 8, 13, "east")
    dummy(d, 14, 8, 13, "west")
    d.set(x2 - 1, 8, z1 + 3, "water_cauldron[level=3]") if False else None
    if L >= 2:                                                    # stands with cantilevered canopy
        for x in range(x1 + 2, x1 + 18):
            if x > x2 - 2:
                break
        n = 0
        for x in range(x1 + 1, x2):
            if n >= 32:
                break
            d.set(x, 8, z1 + 1, "white_concrete")
            d.chair(x, 9, z1 + 1, "north", "birch")
            d.chair(x, 8, z1 + 2, "north", "birch")
            n += 2
        for x in range(x1, x2 + 1):
            for z in range(z1, z1 + 4):
                d.set(x, 12, z, "smooth_quartz_slab[type=bottom,waterlogged=false]")
        for x in (x1, 11, x2):
            for y in range(8, 12):
                d.set(x, y, z1, "light_gray_concrete")
        for x in range(x1 + 2, x2 - 1, 4):
            d.set(x, 11, z1 + 2, "end_rod[facing=down]")
    if L >= 4:                                                    # planters round the court edge
        for z in range(z1 + 5, z2, 3):
            d.set(x2 - 1, 8, z, "azalea")
    # ---- growth: a sports campus round the rooftop arena
    if L >= 2:                                                    # locker rooms and physio
        building(d, 24, 3, 35, 11, nf=1, roof="flat", doors=(("north", 29), ("west", 7)), kinds=["store"])
        d.sign(32, 5, 2, "north", ["", "LOCKERS", "PHYSIO"], "birch", glow=True, color="yellow")
        for x in range(25, 35, 3):
            d.set(x, 1, 1, "moss_block")
            d.set(x, 2, 1, "azalea")
        lamp_post(d, 22, 1)
        lamp_post(d, 37, 1)
    if L >= 3:                                                    # dojo hall with sparring mats
        building(d, 24, 15, 44, 27, nf=2, roof="flat", doors=(("north", 33), ("west", 21)), kinds=["gym", "gym"])
        bench(d, 26, 13, "north", 3)
        bench(d, 36, 13, "north", 3)
    if L >= 4:                                                    # athletes' residence tower
        building(d, 2, 24, 14, 36, nf=3 if L == 4 else 5, roof="flat", doors=(("north", 8), ("east", 30)),
                 kinds=["lounge", "bunks", "bunks", "bunks", "lounge"])
        path(d, 8, 20, 8, 23)
    if L >= 5:                                                    # conditioning centre with a pool
        b = building(d, 17, 31, 44, 44, nf=2, roof="flat", doors=(("north", 22), ("north", 39), ("west", 38)),
                     kinds=["gym", "mess"])
        for x in range(32, 43):
            for z in range(33, 43):
                if d.get(x, 2, z) != AIR and "carpet" not in d.get(x, 2, z):
                    continue
                d.set(x, 1, z, "water[level=0]" if 33 < x < 42 and 34 < z < 42 else "smooth_quartz")
                d.set(x, 2, z, AIR)
        for x in range(18, 44, 4):
            d.set(x, 1, 29, "moss_block")
            d.set(x, 2, 29, "flowering_azalea")
    return d


@design("combatacademy")
def combatacademy(pack, rel, L):
    return tidy({"Hearthwood": ca_hearthwood, "Cascadia": ca_cascadia, "Neoterra": ca_neoterra}[pack](rel, L))


# ================================================================================================ ENCHANTER
"""
Enchanter
  Hearthwood  Scholar's house: timber-framed study with a stone plinth, oriel window and steep tiled roof; the
              enchanting table stands in a ring of bookcases in the ground-floor study, L2+ a book-lined reading
              room upstairs with lecterns, L4 a single-storey library wing, L5 a walled physic garden.
  Cascadia    Mountain library: a long log-walled A-frame hall with a fully glazed front gable and porch; both
              knee walls lined with books, the enchanting circle in the far end under the ridge lanterns; the hall
              grows longer every level.
  Neoterra    Arcane tower: an 11x11 white tower with amethyst-tinted window strips, one book-lined storey per
              level (ladder core), enchanting circle on the ground floor and a crystal crown with end rods.
"""


def ench_ring(d, cx, y, cz, gap="north", h=2):
    """Bookcase ring two blocks out from the enchanting table (valid vanilla layout), one gap to walk in."""
    gx, gz = D4[gap]
    d.item(cx, y, cz, "enchanting_table")
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if max(abs(dx), abs(dz)) != 2:
                continue
            if (dx, dz) == (2 * gx, 2 * gz) or (abs(dx) == 1 and dz == 2 * gz and gz) or \
                    (abs(dz) == 1 and dx == 2 * gx and gx):
                continue
            d.bookshelf(cx + dx, y, cz + dz, h)
    d.set(cx + gx * 2, y + 2, cz + gz * 2, SL("oak", "bottom")) if False else None


def line_walls(d, x1, z1, x2, z2, y, h, skip=()):
    """Line the inner face of a room (x1..x2/z1..z2 are the inner cells) with bookshelves where free."""
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if not (x in (x1, x2) or z in (z1, z2)) or (x, z) in skip:
                continue
            for k in range(h):
                if d.air(x, y + k, z):
                    d.bookshelf(x, y + k, z)


def en_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (44, 30, 34))
    x1, z1, x2, z2 = 3, 3, 13, 11
    d.box(x1, 2, z1, x2, 5, z2, "stone_bricks", floor="spruce_planks")
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if (x in (x1, x2) or z in (z1, z2)) and (x + z) % 3 == 0:
                d.set(x, 3 + (x * z) % 2, z, "mossy_stone_bricks")
    d.fill(x1, 6, z1, x2, 6, z2, "dark_oak_planks")
    if L == 1:
        for x in range(x1, x2 + 1):
            for z in (z1, z2):
                d.set(x, 6, z, LOG("stripped_dark_oak_log", "x"))
        soft(d, d.gable, x1, z1, x2, z2, 7, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite", 1)
    else:
        hw_frame(d, x1, z1, x2, z2, 7, 10)
        soft(d, d.gable, x1, z1, x2, z2, 11, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite", 1)
        d.fill(x1 + 1, 11, z1 + 1, x2 - 1, 11, z2 - 1, "dark_oak_planks")
    # chimney on the west gable
    top = 13 if L == 1 else 17
    for y in range(2, top):
        d.set(x1 - 1, y, 7, "bricks")
    d.set(x1 - 1, 1, 7, "bricks")
    d.set(x1 - 1, top, 7, "brick_wall") if False else None
    # door, oriel bay and windows
    d.door(8, 2, z1, "south", "dark_oak")
    d.set(8, 4, z1, "chiseled_stone_bricks")
    d.sign(10, 4, z1 - 1, "north", ["Lore &", "Enchantment"], "dark_oak")
    for x in (5, 11):
        d.window(x, 3, z1, x, 4, z1)
        d.window(x, 3, z2, x, 4, z2)
    d.window(x2, 3, 7, x2, 4, 7)
    if L >= 2:                                                    # oriel window on brackets
        for x in range(6, 11):
            d.set(x, 7, z1 - 1, "dark_oak_planks")
            d.set(x, 6, z1 - 1, ST("dark_oak", "north", "top"))
            for y in (8, 9):
                d.set(x, y, z1 - 1, "glass_pane" if x not in (6, 10) else LOG("stripped_dark_oak_log"))
            d.set(x, 10, z1 - 1, ST("deepslate_tile", "south"))
            d.set(x, 8, z1, AIR)
            d.set(x, 9, z1, AIR)
        for x in (4, 12):
            d.window(x, 8, z2, x, 9, z2)
    # study: enchanting circle
    ench_ring(d, 8, 2, 7, "north")
    d.set(8, 5, 7, LANT)
    d.hut(x1 + 1, 2, z1 + 1)
    racks = [(x2 - 1, 2, z1 + 1, "west"), (x1 + 1, 2, z2 - 1, "east"), (x1 + 1, 2, z2 - 2, "east"),
             (x1 + 1, 2, z1 + 3, "east"), (x2 - 1, 2, z2 - 1, "west")]
    for x, y, z, f in racks[:d.req["racks"]]:
        d.rack(x, y, z, f)
    d.set(x1 + 1, 2, z1 + 4, "potted_azure_bluet") if False else None
    d.set(x1 + 1, 2, z1 + 2, "chiseled_bookshelf[facing=east,slot_0_occupied=true,slot_1_occupied=true,"
                             "slot_2_occupied=false,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")
    d.rug(7, 6, 9, 8, 2, ("purple_carpet",), "plain") if False else None
    if L >= 2:
        # stairs along the east wall rising south to the reading room
        flight(d, x2 - 1, 2, z1 + 2, "south", 4, "dark_oak", "dark_oak_planks")
        for z in range(z1 + 2, z1 + 5):
            d.set(x2 - 2, 7, z, "dark_oak_fence")
        skip = {(x2 - 1, z) for z in range(z1 + 1, z1 + 8)}
        skip |= {(x, z1 + 1) for x in range(6, 11)}
        line_walls(d, x1 + 1, z1 + 1, x2 - 1, z2 - 1, 7, 3, skip)
        d.item(6, 7, 7, "lectern", "east")
        d.item(10, 7, 7, "lectern", "west")
        d.table(8, 7, 7, "dark_oak", "post")
        d.chair(8, 7, 6, "north", "dark_oak", sit=False)
        d.chair(8, 7, 8, "south", "dark_oak", sit=False)
        d.rug(6, 5, 10, 9, 7, ("purple_carpet", "magenta_carpet"))
        d.chair(7, 7, z1 + 1, "south", "dark_oak", sit=False)
        d.chair(9, 7, z1 + 1, "south", "dark_oak", sit=False)
        d.lamp(8, 10, 5)
        d.lamp(8, 10, 9)
    if L >= 4:                                                    # library wing to the east
        wx1, wx2, wz1, wz2 = x2, 21, 4, 11
        d.box(wx1, 2, wz1, wx2, 5, wz2, "bricks", floor="spruce_planks")
        hw_frame(d, wx1, wz1, wx2, wz2, 4, 5, 2, infill="calcite")
        for x in range(wx1, wx2 + 1):
            for z in (wz1, wz2):
                d.set(x, 2, z, "stone_bricks")
        soft(d, d.gable, wx1, wz1, wx2, wz2, 6, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite", 1)
        d.fill(wx1 + 1, 6, wz1 + 1, wx2 - 1, 6, wz2 - 1, "dark_oak_planks")
        d.set(x2, 2, 9, AIR)
        d.set(x2, 3, 9, AIR)
        for x in (16, 19):
            d.window(x, 3, wz1, x, 4, wz1)
        d.window(wx2, 3, 7, wx2, 4, 8)
        line_walls(d, wx1 + 1, wz1 + 1, wx2 - 1, wz2 - 1, 2, 4 if L >= 5 else 3,
                   {(wx1 + 1, 9), (wx1 + 1, 8), (wx1 + 1, 10)})
        if L >= 5:
            for z in range(z1 + 4, z2):
                for y in (2, 3, 4):
                    if d.air(x1 + 1, y, z):
                        d.bookshelf(x1 + 1, y, z)
        d.dining(16, 2, 7, 3, "x", "dark_oak", ("n", "s"), sit=False)
        for x in (16, 18):
            d.candle(x, 3, 7, 3) if False else None
        d.lamp(17, 5, 7)
    if L >= 5:                                                    # walled physic garden behind
        gx1, gz1, gx2, gz2 = 3, 13, 15, 18
        d.fill(gx1, 1, gz1, gx2, 1, gz2, "grass_block[snowy=false]")
        for x in range(gx1, gx2 + 1):
            for z in range(gz1, gz2 + 1):
                if x in (gx1, gx2) or z == gz2:
                    d.set(x, 2, z, "stone_brick_wall")
        for x in range(gx1 + 2, gx2 - 1, 2):
            for z in (gz1 + 1, gz1 + 3):
                d.set(x, 2, z, ["lilac[half=lower]", "peony[half=lower]", "rose_bush[half=lower]"][x % 3])
                d.set(x, 3, z, ["lilac[half=upper]", "peony[half=upper]", "rose_bush[half=upper]"][x % 3])
        d.door(8, 2, z2, "north", "dark_oak")
        d.fill(8, 1, z2 + 1, 8, 1, gz2 - 1, "gravel")
        d.set(9, 2, gz2 - 1, "stone_brick_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
        d.set(gx1 + 1, 2, gz2 - 1, "oak_sapling[stage=0]") if False else None
    # ---- growth: a small college of lore along the lane
    if L >= 3:                                                    # scriptorium with copyists' desks, archive above
        building(d, 26, 3, 34, 10, nf=2, axis="z", doors=(("north", 30), ("west", 7)), chimney=(35, 7),
                 kinds=["office", "library"])
        d.sign(28, 4, 2, "north", ["Scriptorium"], "dark_oak")
        flowerbed(d, 27, 0, 28, 1)
        flowerbed(d, 32, 0, 33, 1)
        lamp_post(d, 25, 1)
    if L >= 4:                                                    # star tower (observatory) with a weather vane
        t = building(d, 36, 3, 42, 9, nf=3, roof="hip", ground="stone_bricks", doors=(("north", None),),
                     kinds=["library", "office", "office"])
        for y in range(t.ridge + 1, t.ridge + 3):
            d.set(39, y, 6, "iron_bars")
        d.set(39, t.ridge + 3, 6, ROD())
    if L >= 5:                                                    # college hall round a quad
        building(d, 3, 22, 24, 31, nf=2, axis="x", doors=(("north", 13), ("east", 27)), chimney=(2, 27),
                 kinds=["library", "bunks"])
        for x in range(26, 43):
            for z in range(13, 21):
                d.set(x, 1, z, "grass_block[snowy=false]" if (x + z) % 7 else "gravel")
        tree(d, 34, 2, 16, "oak_log", "oak_leaves", 4, 2)
        for x in (28, 40):
            bench(d, x, 19, "south", 2)
        path(d, 26, 12, 42, 12)
    return d


def en_cascadia(rel, L):
    d = Design("Cascadia", rel, (44, 28, 34), paving="coarse_dirt")
    x1, x2, z1 = 3, 13, 3
    Z2 = {1: 12, 2: 15, 3: 18, 4: 23, 5: 28}[L]
    cs_walls(d, x1, z1, x2, Z2, 2, 4)
    d.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, Z2 - 1, "spruce_planks")
    ridge = cs_roof(d, x1, z1, x2, Z2, 5, "z")
    # glazed front gable with log mullions; solid back gable
    for x in range(x1 + 1, x2):
        for y in range(2, ridge):
            if d.get(x, y, z1) in ("minecraft:spruce_planks",) or y <= 4:
                d.set(x, y, z1, LOG("stripped_spruce_log") if x % 3 == 2 else "glass_pane")
    for y in range(2, 5):
        d.set(x1, y, z1, LOG("stripped_spruce_log"))
        d.set(x2, y, z1, LOG("stripped_spruce_log"))
    d.door(8, 2, z1, "south", "spruce")
    for x in range(x1, x2 + 1):
        d.set(x, 5, z1, LOG("spruce_log", "x")) if d.get(x, 5, z1) == "minecraft:glass_pane" else None
    # porch deck
    for x in range(x1, x2 + 1):
        d.set(x, 1, z1 - 1, "spruce_planks")
        d.set(x, 1, z1 - 2, "spruce_planks")
    d.set(x1, 2, z1 - 2, LOG("spruce_log"))
    d.set(x2, 2, z1 - 2, LOG("spruce_log"))
    d.set(x1, 3, z1 - 2, LANT_S)
    d.set(x2, 3, z1 - 2, LANT_S)
    d.sign(8, 2, z1 - 2, "north", ["MOUNTAIN", "LIBRARY"], "spruce") if False else None
    d.set(6, 2, z1 - 1, "spruce_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]")
    d.set(10, 2, z1 - 1, "spruce_stairs[facing=west,half=bottom,shape=straight,waterlogged=false]")
    # inside
    d.hut(x1 + 1, 2, z1 + 1)
    racks = [(x2 - 1, 2, z1 + 1, "west"), (x2 - 1, 2, z1 + 2, "west"), (x1 + 1, 2, z1 + 2, "east"),
             (x2 - 1, 2, z1 + 3, "west"), (x1 + 1, 2, z1 + 3, "east")]
    for x, y, z, f in racks[:d.req["racks"]]:
        d.rack(x, y, z, f)
    cz = Z2 - 3
    ench_ring(d, 8, 2, cz, "north")
    d.rug(7, cz - 1, 9, cz + 1, 2, ("purple_carpet",), "plain") if False else None
    line_walls(d, x1 + 1, z1 + 4, x2 - 1, Z2 - 1, 2, 3,
               {(x, z) for x in range(x1 + 2, x2 - 1) for z in (z1 + 4, Z2 - 1)})
    for z in range(z1 + 6, Z2 - 4, 4):                             # reading desks between the stacks
        d.table(8, 2, z, "spruce", "post")
        d.chair(7, 2, z, "west", "spruce", sit=False)
        d.chair(9, 2, z, "east", "spruce", sit=False)
    if L >= 2:
        d.item(7, 2, z1 + 3, "lectern", "south")
        d.item(9, 2, z1 + 3, "lectern", "south")
    for z in range(z1 + 2, Z2 - 1, 3):
        d.lamp(8, 8, z) if d.air(8, 9, z) or True else None
        d.set(8, 9, z, "chain[axis=y,waterlogged=false]") if d.air(8, 9, z) else None
    d.set(8, 4, Z2, "glass_pane")
    cs_trim(d, x1, z1 + 1, x2, Z2, 2, 4)
    d.sign(8, 4, z1 - 1, "north", ["MOUNTAIN", "LIBRARY"], "spruce") if False else None
    d.set(8, 5, Z2, "glass_pane") if d.get(8, 5, Z2) == "minecraft:spruce_planks" else None
    # stone chimney stove on the east wall at the front
    d.set(x2 + 1, 1, z1 + 5, "cobblestone")
    for y in range(2, ridge - 1):
        d.set(x2 + 1, y, z1 + 5, "mossy_cobblestone" if y % 3 == 0 else "cobblestone")
    if L >= 3:                                                    # moss and ferns along the eaves
        for z in range(z1, Z2 + 1, 2):
            d.set(x1 - 2, 2, z, "fern") if d.bp.inside(x1 - 2, 2, z) else None
            d.set(x2 + 2, 2, z, "fern") if z != z1 + 5 else None
    if L >= 5:
        for z in (Z2 + 1,):
            for x in range(x1, x2 + 1, 2):
                d.set(x, 2, z, "spruce_fence")
    # ---- growth: a mountain retreat of scholars
    if L >= 2:                                                    # scribe's cabin (L3: loft)
        building(d, 20, 3, 28, 9, nf=1 if L == 2 else 2, axis="x", doors=(("north", 24), ("west", 6)),
                 chimney=(29, 6), kinds=["office", "bunks"])
        bench(d, 21, 2, "south", 2)
        lamp_post(d, 18, 1)
    if L >= 3:                                                    # bindery with a drying porch
        building(d, 20, 13, 30, 20, nf=1, axis="z", doors=(("north", 25),), kinds=["workshop"])
        for z in range(13, 21):
            d.set(31, 1, z, "spruce_planks")
            d.set(32, 1, z, "spruce_planks")
            d.set(32, 5, z, ST("spruce", "east"))
            d.set(31, 5, z, SL("spruce", "top"))
        drying_beam(d, 31, 31, 16, 4, "stripped_spruce_log") if False else None
    if L >= 4:                                                    # star-gazing lookout
        t = building(d, 34, 3, 40, 9, nf=4, roof="hip", doors=(("north", None),),
                     kinds=["library", "office", "bunks", "office"])
        for y in range(t.ridge + 1, t.ridge + 3):
            d.set(37, y, 6, "spruce_fence")
        d.set(37, t.ridge + 3, 6, "lantern[hanging=false,waterlogged=false]")
        for x in range(33, 42):                                   # wrap-around deck at the foot
            for z in (11, 12):
                d.set(x, 1, z, "spruce_planks")
            d.set(x, 2, 12, "spruce_fence")
        d.set(37, 2, 12, AIR)
    if L >= 5:                                                    # guest lodge for visiting scholars
        building(d, 20, 23, 38, 31, nf=2, axis="x", doors=(("north", 29), ("west", 27)), chimney=(39, 27),
                 kinds=["lounge", "bunks"])
        for z in range(12, 33, 5):
            tree(d, 42, 2, z, "spruce_log", "spruce_leaves", 7, 2, cone=True)
    return d


def en_neoterra(rel, L):
    d = Design("Neoterra", rel, (32, 34, 32), paving="smooth_stone")
    x1, z1, x2, z2 = 4, 4, 14, 14
    nf = {1: 1, 2: 2, 3: 2, 4: 3, 5: 4}[L]
    H = 5
    top = 2 + nf * H                                              # roof deck y
    nt_walls(d, x1, z1, x2, z2, 2, top - 1)
    d.fill(x1, 1, z1, x2, 1, z2, "polished_diorite")
    for i in range(1, nf):
        d.fill(x1 + 1, 2 + i * H - 1, z1 + 1, x2 - 1, 2 + i * H - 1, z2 - 1, "light_gray_concrete")
        for x in range(x1, x2 + 1):
            for z in (z1, z2):
                d.set(x, 2 + i * H - 1, z, "purpur_block")
        for z in range(z1, z2 + 1):
            for x in (x1, x2):
                d.set(x, 2 + i * H - 1, z, "purpur_block")
    d.flat(x1, z1, x2, z2, top, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
    # amethyst-tinted window strips up the middle of every face
    for y in range(3, top - 1):
        if (y - 2) % H == H - 1:
            continue
        for c in (8, 10):
            d.set(c, y, z2, "purple_stained_glass_pane")
            d.set(x1, y, c, "purple_stained_glass_pane")
            d.set(x2, y, c, "purple_stained_glass_pane")
            if y > 5:
                d.set(c, y, z1, "purple_stained_glass_pane")
    d.double_door(8, 2, z1, "x", "south", "birch")
    d.door(10, 2, z1, "south", "birch") if False else None
    for x in range(7, 12):
        d.set(x, 5, z1 - 1, SL("smooth_quartz", "top"))
    d.sign(10, 4, z1 - 1, "north", ["", "ARCANUM"], "birch", glow=True, color="magenta")
    # ground floor: enchanting circle
    ench_ring(d, 9, 2, 9, "north")
    d.set(9, 5, 9, "end_rod[facing=down]")
    d.hut(x1 + 1, 2, z1 + 1)
    racks = [(x2 - 1, 2, z1 + 1, "west"), (x1 + 1, 2, z2 - 1, "east"), (x1 + 1, 2, 9, "east"),
             (x2 - 1, 2, 9, "west"), (9, 2, z2 - 1, "north")]
    for x, y, z, f in racks[:d.req["racks"]]:
        d.rack(x, y, z, f)
    d.plant(x1 + 1, 2, z1 + 3, "potted_bamboo")
    for x, z in ((x1 + 2, z1 + 2), (x2 - 2, z1 + 2), (x1 + 2, z2 - 2), (x2 - 2, z2 - 2)):
        d.set(x, 5, z, "sea_lantern")
    # ladder core in the south-east corner
    lx, lz = x2 - 1, z2 - 1
    ladder(d, lx, lz, 2, top - H - 1 if nf > 1 else 2, "west")
    for i in range(1, nf):
        y = 2 + i * H
        line_walls(d, x1 + 1, z1 + 1, x2 - 1, z2 - 1, y, 3, {(lx, lz), (lx - 1, lz), (lx, lz - 1)})
        d.set(9, y, 9, "amethyst_block")
        d.set(9, y + 1, 9, "amethyst_cluster[facing=up,waterlogged=false]")
        if i == 1:
            d.item(7, y, 9, "lectern", "east")
            d.item(11, y, 9, "lectern", "west")
        else:
            d.chair(8, y, 7, "north", "birch", sit=False)
            d.chair(10, y, 7, "north", "birch", sit=False)
            d.set(9, y, 7, SL("smooth_quartz", "top"))
        d.rug(7, 7, 11, 11, y, ("magenta_carpet", "purple_carpet"))
        for x, z in ((7, 7), (11, 7), (7, 11), (11, 11)):
            d.set(x, y + 3, z, "sea_lantern")
    # crystal crown on the roof
    for x in range(7, 12):
        for z in range(7, 12):
            if abs(x - 9) + abs(z - 9) <= 2:
                d.set(x, top + 1, z, "amethyst_block")
    d.set(9, top + 2, 9, "budding_amethyst")
    d.set(9, top + 3, 9, "amethyst_cluster[facing=up,waterlogged=false]")
    for x, z in ((x1 + 1, z1 + 1), (x2 - 1, z1 + 1), (x1 + 1, z2 - 1), (x2 - 1, z2 - 1)):
        d.set(x, top + 1, z, ENDROD())
    if L >= 3:                                                    # planters round the tower foot
        for x in range(x1 - 2, x2 + 3):
            for z in (z1 - 2, z2 + 2):
                if x not in (8, 9, 10) or z == z2 + 2:
                    d.set(x, 1, z, "moss_block")
                    if x % 3 == 0:
                        d.set(x, 2, z, "azalea")
    # ---- growth: an arcane institute round the tower
    if L >= 3:                                                    # library annex linked to the tower
        building(d, 17, 4, 29, 14, nf=2, roof="flat", doors=(("north", 23), ("west", 9)),
                 kinds=["library", "library"])
        d.set(x2, 2, 9, AIR) if False else None
        d.sign(26, 5, 3, "north", ["", "LIBRARY"], "birch", glow=True, color="magenta")
        lamp_post(d, 16, 1)
        lamp_post(d, 30, 1)
    if L >= 4:                                                    # observatory with a glass dome
        ob = building(d, 17, 18, 29, 28, nf=1, roof="flat", doors=(("north", 23), ("west", 23)), kinds=["office"],
                      flat_deco=False)
        cx, cz, r = 23, 23, 4
        for x in range(cx - r, cx + r + 1):
            for z in range(cz - r, cz + r + 1):
                for y in range(ob.top + 1, ob.top + r + 2):
                    dd = ((x - cx) ** 2 + (z - cz) ** 2 + (y - ob.top - 1) ** 2) ** 0.5
                    if r - 0.6 <= dd < r + 0.4:
                        d.set(x, y, z, "purple_stained_glass" if (x + z + y) % 3 else "white_concrete")
        for y in range(ob.top + 1, ob.top + 4):
            d.set(cx, y, cz, "iron_bars")
        d.set(cx, ob.top + 4, cz, ENDROD("north"))
        for x in range(18, 29, 3):
            d.set(x, 1, 16, "moss_block")
            d.set(x, 2, 16, "flowering_azalea")
    if L >= 5:                                                    # scriptorium and dormitory for adepts
        building(d, 2, 20, 14, 30, nf=3, roof="flat", doors=(("north", 8), ("east", 25)),
                 kinds=["library", "office", "bunks"])
        for z in range(18, 31, 3):
            d.set(16, 1, z, "moss_block")
            d.set(16, 2, z, "azalea")
    return d


@design("enchanter")
def enchanter(pack, rel, L):
    return tidy({"Hearthwood": en_hearthwood, "Cascadia": en_cascadia, "Neoterra": en_neoterra}[pack](rel, L))


# ================================================================================================ ALCHEMIST
"""
Alchemist
  Hearthwood  Apothecary: narrow gable-fronted shop with leaded shop windows full of potted herbs and a hanging
              sign; shop counter at the front, brewing bench and island behind with herb-drying beams hung with
              roots; L2+ timber-framed drying loft with stores upstairs, L3+ walled herb garden with nether wart
              beds, L4+ a glass lean-to greenhouse, L5 flower boxes.
  Cascadia    Herbalist's cabin: long low log cabin with a deep porch hung with drying racks, a cobble hearth with
              the cauldron over the fire, brewing bench along the back wall; grows along x, L4+ moss-roofed
              potting shed and raised beds, L5 greenhouse.
  Neoterra    Pharmacy lab: white flat-roofed storefront with a glowing green cross, glass counter and a glazed lab
              behind with quartz benches, a fume hood and grow-light planters; L3 wider, L4+ rooftop greenhouse.
"""


def drying_beam(d, x1, x2, z, y, beam):
    """Herb-drying rack: a beam under the ceiling with roots and vines hanging from it."""
    for x in range(x1, x2 + 1):
        d.set(x, y, z, LOG(beam, "x"))
        if d.air(x, y - 1, z):
            d.set(x, y - 1, z, "hanging_roots[waterlogged=false]" if x % 2 else
                  "cave_vines_plant[berries=false]" if False else "hanging_roots[waterlogged=false]")


def al_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (43, 26, 37))
    x1, x2, z1, z2 = 4, 12, 3, 12
    d.box(x1, 2, z1, x2, 5, z2, "calcite", floor="oak_planks")
    hw_frame(d, x1, z1, x2, z2, 2, 5, 2)
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                d.set(x, 1, z, "stone_bricks")
    d.fill(x1, 6, z1, x2, 6, z2, "dark_oak_planks")
    if L == 1:
        soft(d, d.gable, x1, z1, x2, z2, 7, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite", 1)
    else:
        hw_frame(d, x1, z1, x2, z2, 7, 10, 2)
        soft(d, d.gable, x1, z1, x2, z2, 11, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "calcite", 1)
        for x in (6, 10):
            d.window(x, 8, z1, x, 9, z1)
            d.window(x, 8, z2, x, 9, z2)
        d.window(x1, 8, 7, x1, 9, 7)
        d.window(x2, 8, 9, x2, 9, 9)
    # brick chimney on the east side
    for y in range(1, 15 if L > 1 else 12):
        d.set(x2 + 1, y, 9, "bricks")
    # shop front: door + two shop windows with display sills
    d.door(8, 2, z1, "south", "dark_oak")
    for xs in ((5, 6, 7), (9, 10, 11)):
        for x in xs:
            d.window(x, 3, z1, x, 4, z1)
            d.set(x, 2, z1 + 1, SL("dark_oak", "top"))
            d.set(x, 3, z1 + 1, ["potted_fern", "decorated_pot[cracked=false,facing=south,waterlogged=false]",
                                 "potted_allium"][x % 3])
        d.set(xs[0], 2, z1 - 1, TD("dark_oak", "north", "top", "true"))
    for x in (5, 7, 9, 11):
        d.set(x, 2, z1 - 1, "potted_red_tulip" if x % 4 == 1 else "potted_blue_orchid")
    d.sign(10, 5, z1 - 1, "east", ["Apothecary", "Tinctures &", "Remedies"], "dark_oak", hanging=True)
    d.set(11, 5, z1 - 1, "dark_oak_planks")
    d.window(x1, 3, 9, x1, 4, 9)
    d.window(x2, 3, 6, x2, 4, 6)
    d.window(7, 3, z2, 7, 4, z2)
    # shop: counter with a scale (pots) and the hut
    d.hut(x1 + 1, 2, 5)
    for x in range(5, 10):
        d.set(x, 2, 7, SL("dark_oak", "top") if x != 7 else "dark_oak_planks")
    d.set(6, 3, 7, "decorated_pot[cracked=false,facing=north,waterlogged=false]")
    d.set(8, 3, 7, "potted_brown_mushroom")
    d.chair(7, 2, 5, "south", "dark_oak", sit=False) if False else None
    d.set(x2 - 1, 2, 5, "chiseled_bookshelf[facing=west,slot_0_occupied=true,slot_1_occupied=true,"
                        "slot_2_occupied=false,slot_3_occupied=true,slot_4_occupied=true,slot_5_occupied=false]")
    d.lamp(8, 5, 5)
    # workshop: brewing bench, island, cauldron, racks
    d.item(5, 2, 11, "water_cauldron[level=3]")
    for x in range(6, 10):
        d.set(x, 2, 11, "dark_oak_planks")
    stands = [(6, 3, 11), (8, 3, 11), (7, 3, 9), (9, 3, 11), (8, 3, 9)]
    d.set(7, 2, 9, "dark_oak_planks")
    d.set(8, 2, 9, "dark_oak_planks")
    for i, (x, y, z) in enumerate(stands):
        if i < L:
            d.item(x, y, z, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
        else:
            d.set(x, y, z, "potted_crimson_fungus" if i % 2 else "flower_pot")
    racks = [(5, 2, 9, "east"), (5, 2, 10, "east"), (5, 7, 9, "east"), (5, 7, 10, "east"), (5, 7, 11, "east")]
    if L == 1:
        racks = racks[:1]
    nground = 2
    for i, (x, y, z, f) in enumerate(racks[:d.req["racks"]]):
        d.rack(x, y, z, f)
    drying_beam(d, 6, 10, 10, 5, "stripped_dark_oak_log")
    d.lamp(7, 5, 8)
    if L >= 2:
        flight(d, 11, 2, 11, "north", 4, "dark_oak", "dark_oak_planks")
        for z in range(9, 12):
            d.set(10, 7, z, "dark_oak_fence")
        # drying loft upstairs
        drying_beam(d, 6, 9, 5, 10, "stripped_dark_oak_log")
        drying_beam(d, 6, 9, 7, 10, "stripped_dark_oak_log")
        for x in (6, 7, 8):
            d.set(x, 7, 4, "barrel[facing=north,open=false]" if x == 7 else "decorated_pot[cracked=false,facing=south,waterlogged=false]")
        d.set(x2 - 1, 7, 4, "chest[facing=west,type=single,waterlogged=false]")
        d.table(9, 7, 6, "dark_oak")
        d.candle(9, 8, 6, 3) if False else None
        d.chair(9, 7, 7, "south", "dark_oak", sit=False)
        d.lamp(8, 10, 9)
    if L >= 3:                                                    # walled herb garden
        gx1, gz1, gx2, gz2 = 3, 13, 15, 21
        d.fill(gx1, 1, gz1, gx2, 1, gz2, "grass_block[snowy=false]")
        for x in range(gx1, gx2 + 1):
            for z in range(gz1, gz2 + 1):
                if x in (gx1, gx2) or z == gz2:
                    d.set(x, 2, z, "brick_wall")
        d.door(8, 2, z2, "north", "dark_oak")
        for z in range(z2 + 1, gz2):
            d.set(8, 1, z, "gravel")
        for x in list(range(gx1 + 2, 7)) + list(range(10, gx2 - 1)):
            for z in (15, 16, 18, 19):
                if z in (15, 16):
                    d.set(x, 1, z, "soul_sand")
                    d.set(x, 2, z, "nether_wart[age=3]")
                else:
                    d.set(x, 1, z, "farmland[moisture=7]")
                    d.set(x, 2, z, "beetroots[age=3]" if x % 2 else "carrots[age=7]")
        d.set(gx2 - 1, 2, gz1 + 1, "composter[level=4]")
        d.set(gx1 + 1, 2, gz2 - 1, "water_cauldron[level=3]")
    if L >= 4:                                                    # glass lean-to greenhouse on the west
        hx1, hx2 = 0, x1
        for z in range(5, 11):
            d.set(1, 1, z, "stone_bricks")
            d.set(1, 2, z, "stone_bricks")
            d.set(1, 3, z, "glass_pane")
            d.set(2, 4, z, "glass")
            d.set(3, 5, z, "glass")
            d.set(2, 1, z, "farmland[moisture=7]")
            d.set(2, 2, z, ["allium", "azure_bluet", "cornflower", "lily_of_the_valley"][z % 4])
            d.set(3, 1, z, "oak_planks")
        for x in (1, 2, 3):
            for y in range(2, 6 - (3 - x)):
                d.set(x, y, 4, "glass_pane" if x > 1 else "stone_bricks")
                d.set(x, y, 11, "glass_pane" if x > 1 else "stone_bricks")
        d.set(1, 3, 4, "glass_pane")
        d.set(1, 3, 11, "glass_pane")
        d.set(x1, 2, 7, AIR)
        d.set(x1, 3, 7, AIR)
        d.set(x1, 4, 7, "stripped_dark_oak_log[axis=y]") if False else None
    if L >= 5:
        for x in (6, 10):
            d.set(x, 7, z1 - 1, TD("dark_oak", "north", "top", "true"))
        d.set(8, 4, z1 - 1, "lantern[hanging=false,waterlogged=false]") if False else None
        d.wall_torch(7, 4, z1 - 1, "north")
        d.wall_torch(9, 4, z1 - 1, "north")
    # ---- growth: an apothecaries' row with a physic garden
    if L >= 2:                                                    # still-house for distilling cordials
        building(d, 17, 4, 24, 11, nf=1, axis="z", doors=(("north", 20),), chimney=(25, 8), kinds=["lab"])
        d.sign(22, 4, 3, "north", ["Still", "House"], "dark_oak")
        lamp_post(d, 15, 1)
    if L >= 3:                                                    # herbalist's cottage (two storeys)
        building(d, 27, 3, 35, 10, nf=2, axis="x", doors=(("north", 31), ("west", 7)), chimney=(36, 7),
                 kinds=["kitchen", "bunks"])
        flowerbed(d, 28, 0, 29, 1)
        flowerbed(d, 33, 0, 34, 1)
        d.set(31, 1, 1, "gravel")
        d.set(31, 1, 0, "gravel")
    if L >= 4:                                                    # drying barn for herbs, store above
        building(d, 17, 24, 30, 31, nf=2, axis="x", doors=(("north", 23), ("west", 28)), kinds=["store", "store"])
        for x in range(18, 30, 3):
            drying_beam(d, x, x + 1, 23, 5, "stripped_dark_oak_log") if False else None
    if L >= 5:                                                    # guild hall of apothecaries
        building(d, 27, 13, 40, 21, nf=2, axis="x", doors=(("north", 33), ("west", 17)), chimney=(41, 17),
                 kinds=["library", "office"])
        building(d, 32, 24, 40, 31, nf=1, axis="z", doors=(("north", 36),), kinds=["lab"])
        for x in (36, 38):
            tree(d, x, 2, 34, "oak_log", "flowering_azalea_leaves", 3, 1)
    return d


def al_cascadia(rel, L):
    d = Design("Cascadia", rel, (37, 26, 35), paving="coarse_dirt")
    x1, z1, z2 = 3, 6, 12
    X2 = {1: 11, 2: 13, 3: 15, 4: 15, 5: 15}[L]
    cs_walls(d, x1, z1, X2, z2, 2, 5)
    d.fill(x1 + 1, 1, z1 + 1, X2 - 1, 1, z2 - 1, "spruce_planks")
    ridge = cs_roof(d, x1, z1, X2, z2, 6, "x")
    d.fill(x1 + 1, 6, z1 + 1, X2 - 1, 6, z2 - 1, "spruce_planks")
    for x in range(x1 - 1, X2 + 2):                               # moss on the eaves
        d.set(x, 5, z2 + 1, "moss_carpet") if False else None
    # porch with drying racks
    for x in range(x1, X2 + 1):
        for z in range(z1 - 3, z1):
            d.set(x, 1, z, "spruce_planks")
        d.set(x, 5, z1 - 3, ST("spruce", "south"))
        d.set(x, 5, z1 - 2, SL("spruce", "top"))
        d.set(x, 5, z1 - 1, SL("spruce", "top"))
    for x in range(x1, X2 + 1, 4):
        for y in range(2, 5):
            d.set(x, y, z1 - 3, LOG("spruce_log"))
    drying_beam(d, x1 + 1, x1 + 3, z1 - 2, 4, "stripped_spruce_log")
    drying_beam(d, X2 - 3, X2 - 1, z1 - 2, 4, "stripped_spruce_log")
    for x in range(x1 + 1, X2):
        if x % 4 and d.air(x, 2, z1 - 3):
            d.set(x, 2, z1 - 3, "spruce_fence")
    door = 7
    d.door(door, 2, z1, "south", "spruce")
    d.set(door, 2, z1 - 3, AIR)
    d.set(door + 1, 2, z1 - 1, "potted_fern")
    d.set(door - 1, 2, z1 - 1, "barrel[facing=up,open=false]") if False else None
    for x in range(x1 + 2, X2 - 1, 4):
        if x != door:
            d.window(x, 3, z1, x + 1 if x + 1 != door else x, 4, z1)
    d.window(x1, 3, 9, x1, 4, 9)
    d.sign(door + 1, 4, z1 - 1, "north", ["HERBS &", "TONICS"], "spruce")
    cs_trim(d, x1, z1, X2, z2, 2, 5)
    d.set(door - 1, 4, z1 - 1, LANT) if False else None
    # hearth with the cauldron over the fire, chimney through the roof
    hx = X2 - 2
    for x in (hx - 1, hx + 1):
        for y in (2, 3, 4):
            d.set(x, y, z2 - 1, "cobblestone")
    d.set(hx, 2, z2 - 1, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    d.item(hx, 3, z2 - 1, "water_cauldron[level=3]")
    d.set(hx, 4, z2 - 1, "cobblestone")
    for y in range(1, ridge + 2):
        d.set(hx, y, z2, "mossy_cobblestone" if y % 3 == 0 else "cobblestone")
    for y in range(5, 7):
        d.set(hx, y, z2 - 1, "cobblestone")
    # brewing bench along the back wall
    d.hut(x1 + 1, 2, z1 + 1)
    for x in range(x1 + 1, hx - 1):
        d.set(x, 2, z2 - 1, SL("spruce", "top"))
    stands = [(x1 + 2, 3, z2 - 1), (x1 + 4, 3, z2 - 1), (x1 + 3, 3, z2 - 1), (x1 + 5, 3, z2 - 1), (x1 + 6, 3, z2 - 1)]
    for i, (x, y, z) in enumerate(stands):
        if i < L:
            d.item(x, y, z, "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]")
        elif "slab" in d.get(x, y - 1, z) and d.air(x, y, z):
            d.set(x, y, z, "flower_pot" if i % 2 else "potted_red_mushroom")
    racks = [(x1 + 1, 2, z1 + 3, "east"), (x1 + 1, 2, z1 + 4, "east"), (x1 + 2, 2, z1 + 1, "south"),
             (x1 + 3, 2, z1 + 1, "south"), (x1 + 1, 2, z1 + 2, "east")]
    for x, y, z, f in racks[:d.req["racks"]]:
        d.rack(x, y, z, f)
    d.table(x1 + 4, 2, z1 + 3, "spruce")
    d.chair(x1 + 5, 2, z1 + 3, "east", "spruce", sit=False)
    drying_beam(d, x1 + 2, X2 - 4, z1 + 3, 5, "stripped_spruce_log")
    d.lamp(X2 - 3, 5, z1 + 2)
    d.rug(X2 - 4, z1 + 2, X2 - 2, z1 + 3, 2, ("green_carpet",), "plain")
    if L >= 4:                                                    # raised beds with mushrooms & berries
        for x in range(4, 14, 3):
            for dx in (0, 1):
                d.set(x + dx, 1, 15, "spruce_planks")
                d.set(x + dx, 2, 15, "podzol")
                d.set(x + dx, 3, 15, "sweet_berry_bush[age=3]" if x % 2 else "fern")
                d.set(x + dx, 1, 17, "spruce_planks")
                d.set(x + dx, 2, 17, "mycelium[snowy=false]")
                d.set(x + dx, 3, 17, "red_mushroom" if dx else "brown_mushroom")
        d.set(3, 2, 18, "composter[level=6]")
    if L >= 5:                                                    # greenhouse on the east end
        gx1, gx2 = X2, 22
        for x in range(gx1, gx2 + 1):
            for z in range(z1, z2 + 1):
                d.set(x, 1, z, "cobblestone" if x in (gx1, gx2) or z in (z1, z2) else "farmland[moisture=7]")
                edge = x in (gx1, gx2) or z in (z1, z2)
                if x == gx1:
                    continue
                if edge:
                    d.set(x, 2, z, LOG("spruce_log") if x == gx2 and z in (z1, z2) else "glass_pane")
                    d.set(x, 3, z, "glass_pane")
                    d.set(x, 4, z, "glass_pane")
                else:
                    d.set(x, 2, z, ["lily_of_the_valley", "allium", "blue_orchid", "oxeye_daisy"][(x + z) % 4]
                          if z != 9 else AIR)
                    if z == 9:
                        d.set(x, 1, z, "spruce_planks")
                d.set(x, 5, z, "glass")
        d.set(X2, 2, 9, AIR)
        d.set(X2, 3, 9, AIR)
    # ---- growth: a forest herb farm
    if L >= 2:                                                    # root cellar & seed store
        building(d, 3, 15, 10, 20, nf=1, axis="x", doors=(("north", 6),), kinds=["store"])
        lamp_post(d, 12, 15)
    if L >= 3:                                                    # tincture workshop with a loft
        building(d, 18, 15, 26, 21, nf=2, axis="z", doors=(("north", 22),), chimney=(27, 18), kinds=["lab", "store"])
        cart(d, 13, 18, "z")
    if L >= 4:                                                    # bunk cabin for the pickers
        building(d, 3, 24, 13, 31, nf=2, axis="x", doors=(("north", 8),), chimney=(14, 27), kinds=["kitchen", "bunks"])
        for x in range(3, 14):
            d.set(x, 1, 23, "spruce_planks")
            d.set(x, 1, 22, "spruce_planks")
            d.set(x, 5, 22, SL("spruce", "top"))
            d.set(x, 5, 23, SL("spruce", "top"))
        for x in (3, 8, 13):
            for y in (2, 3, 4):
                d.set(x, y, 22, LOG("spruce_log"))
    if L >= 5:                                                    # trading post for remedies
        building(d, 17, 25, 30, 32, nf=2, axis="x", doors=(("north", 23), ("west", 29)), chimney=(31, 29),
                 kinds=["office", "lounge"])
        for z in range(3, 33, 6):
            tree(d, 34, 2, z, "spruce_log", "spruce_leaves", 7, 2, cone=True)
    return d


def al_neoterra(rel, L):
    d = Design("Neoterra", rel, (40, 26, 39), paving="smooth_stone")
    x1, z1, z2 = 2, 3, 13
    X2 = 12 if L < 3 else 16
    nt_walls(d, x1, z1, X2, z2, 2, 6)
    d.fill(x1, 1, z1, X2, 1, z2, "polished_diorite")
    d.flat(x1, z1 - 1, X2, z2, 7, "smooth_quartz", "white_concrete", "smooth_quartz_slab")
    for x in range(x1, X2 + 1):
        d.set(x, 7, z1 - 1, "lime_terracotta")
    for x in range(x1 + 1, X2):
        d.window(x, 2, z1, x, 5, z1, "glass_pane")
    d.double_door(6, 2, z1, "x", "south", "birch")
    # glowing green cross sign
    cx, cy = X2 - 2, 9
    for x, y in ((cx, cy - 1), (cx, cy), (cx, cy + 1), (cx - 1, cy), (cx + 1, cy)):
        d.set(x, y, z1 - 1, "lime_concrete")
    d.set(cx, cy, z1 - 1, "verdant_froglight[axis=y]")
    d.set(cx, 7, z1 - 1, "white_concrete") if False else None
    d.sign(4, 6, z1 - 1, "north", ["", "PHARMACY"], "birch", glow=True, color="lime")
    # store: glass counter and shelves
    d.hut(x1 + 1, 2, z1 + 1)
    for x in range(x1 + 1, X2):
        if x in (8,):
            continue
        d.set(x, 2, z1 + 4, "smooth_quartz")
        d.set(x, 3, z1 + 4, "light_blue_stained_glass_pane") if x % 2 else None
    for z in range(z1 + 1, z1 + 4):
        d.set(X2 - 1, 2, z, SL("smooth_quartz", "top"))
        d.set(X2 - 1, 3, z, ["potted_allium", "decorated_pot[cracked=false,facing=west,waterlogged=false]",
                             "potted_azure_bluet"][z % 3])
    for x in range(x1 + 2, X2, 3):
        d.set(x, 6, z1 + 2, "sea_lantern")
    # lab behind a glass partition
    for x in range(x1 + 1, X2):
        d.set(x, 2, z1 + 6, "white_concrete" if x != 8 else AIR)
        for y in (3, 4):
            d.set(x, y, z1 + 6, "light_gray_stained_glass_pane" if x != 8 else AIR)
        d.set(x, 5, z1 + 6, "white_concrete")
        d.set(x, 6, z1 + 6, "white_concrete")
    d.door(8, 2, z1 + 6, "north", "birch")
    for x in range(x1 + 1, X2):                                   # quartz bench on the back wall
        d.set(x, 2, z2 - 1, "smooth_quartz")
    stands = [(x1 + 2, 3, z2 - 1), (x1 + 4, 3, z2 - 1), (x1 + 6, 3, z2 - 1), (x1 + 8, 3, z2 - 1),
              (x1 + 3, 3, z2 - 1)]
    for i, (x, y, z) in enumerate(stands):
        if i < L:
            d.item(x, y, z, "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=true]")
    # fume hood over the bench, sink (cauldron)
    for x in range(x1 + 1, x1 + 10):
        d.set(x, 5, z2 - 1, "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    d.item(X2 - 1, 2, z2 - 1, "water_cauldron[level=3]")
    d.set(X2 - 1, 3, z2, "lever[face=wall,facing=north,powered=false]") if False else None
    racks = [(x1 + 1, 2, z1 + 7, "east"), (x1 + 1, 2, z1 + 8, "east"), (X2 - 1, 2, z1 + 7, "west"),
             (X2 - 1, 2, z1 + 8, "west"), (x1 + 1, 2, z1 + 2, "east")]
    for x, y, z, f in racks[:d.req["racks"]]:
        d.rack(x, y, z, f)
    # grow-light planters
    for x in range(x1 + 3, x1 + 6):
        d.set(x, 2, z1 + 7, "moss_block")
        d.set(x, 3, z1 + 7, ["lily_of_the_valley", "fern", "allium", "blue_orchid"][x % 4])
        d.set(x, 6, z1 + 7, "end_rod[facing=down]")
    for x in range(x1 + 2, X2, 3):
        d.set(x, 6, z2 - 2, "sea_lantern")
    for z in range(z1 + 7, z2, 3):
        d.window(x1, 3, z, x1, 5, z)
        d.window(X2, 3, z, X2, 5, z)
    if L >= 4:                                                    # rooftop greenhouse
        gx1, gz1, gx2, gz2 = x1 + 1, z1 + 3, x1 + 9, z2 - 1
        for x in range(gx1, gx2 + 1):
            for z in range(gz1, gz2 + 1):
                if x in (gx1, gx2) or z in (gz1, gz2):
                    for y in (8, 9, 10):
                        d.set(x, y, z, "glass_pane" if not (x in (gx1, gx2) and z in (gz1, gz2)) else "white_concrete")
                elif z != (gz1 + gz2) // 2:
                    d.set(x, 8, z, ["allium", "azure_bluet", "cornflower", "lily_of_the_valley"][(x + z) % 4])
                    d.set(x, 7, z, "moss_block")
        d.fill(gx1, 11, gz1, gx2, 11, gz2, "glass")
        d.door(gx2, 8, (gz1 + gz2) // 2, "east", "birch")
        ladder(d, X2 + 1, z2 - 2, 2, 7, "east")
        d.set(X2, 8, z2 - 2, AIR)
        d.set(X2, 9, z2 - 2, AIR)
    # ---- growth: a pharmaceutical research campus
    if L >= 2:                                                    # glasshouse for medicinal plants
        gx1, gz1, gx2, gz2 = 20, 3, 28, 11
        for x in range(gx1, gx2 + 1):
            for z in range(gz1, gz2 + 1):
                edge = x in (gx1, gx2) or z in (gz1, gz2)
                d.set(x, 1, z, "polished_andesite" if edge else ("smooth_stone" if z == 7 or x == 24 else "moss_block"))
                if edge:
                    for y in range(2, 6):
                        d.set(x, y, z, "white_concrete" if (x in (gx1, gx2) and z in (gz1, gz2)) else "glass_pane")
                elif z != 7 and x != 24:
                    d.set(x, 2, z, ["lily_of_the_valley", "allium", "fern", "azure_bluet", "blue_orchid"][(x + z) % 5])
                for y in (6,):
                    d.set(x, y, z, "glass" if not edge else "white_concrete")
        d.door(24, 2, gz1, "south", "birch")
        for x in range(gx1 + 2, gx2 - 1, 3):
            d.set(x, 5, 5, "end_rod[facing=down]")
            d.set(x, 5, 9, "end_rod[facing=down]")
        lamp_post(d, 18, 1)
    if L >= 3:                                                    # research labs
        building(d, 20, 15, 34, 25, nf=2, roof="flat", doors=(("north", 26), ("west", 20)), kinds=["lab", "lab"])
        d.sign(31, 5, 14, "north", ["", "R&D LABS"], "birch", glow=True, color="lime")
        bench(d, 22, 13, "north", 2)
    if L >= 4:                                                    # compounding plant
        building(d, 2, 17, 16, 27, nf=2, roof="flat", doors=(("north", 9), ("east", 22)), kinds=["store", "workshop"])
        for x in range(3, 16, 4):
            d.set(x, 1, 15, "moss_block")
            d.set(x, 2, 15, "azalea")
    if L >= 5:                                                    # teaching pharmacy and staff residence
        building(d, 2, 29, 20, 37, nf=3, roof="flat", doors=(("north", 11), ("east", 33)),
                 kinds=["lounge", "office", "bunks"])
        building(d, 24, 28, 38, 37, nf=2, roof="flat", doors=(("north", 31),), kinds=["lab", "library"])
    return d


@design("alchemist")
def alchemist(pack, rel, L):
    return tidy({"Hearthwood": al_hearthwood, "Cascadia": al_cascadia, "Neoterra": al_neoterra}[pack](rel, L))


# ================================================================================================ GRAVEYARD
"""
Graveyard
  Hearthwood  Village churchyard: mossy stone wall with a roofed oak lychgate on the street, gravel path to a
              small stone chapel (pews, altar, vestry rack) at the back, rows of headstones either side; L3+
              bell-cote, L4+ yew trees, L5 lanterns along the path.
  Cascadia    Pioneer cemetery: split-rail fence with a log gate arch, caretaker's log chapel with a porch bench
              on the west, graves in a grid among tall spruces on the east, lanterns on posts.
  Neoterra    Memorial park: low concrete-and-glass columbarium pavilion with benches facing a reflecting pool,
              graves in a neat lawn grid on smooth paths, birch trees and lit bollards.
"""
NAMES_G = ["Ada Fletcher", "Tom Mason", "Mary Cooper", "Will Baker", "Ann Smith", "John Miller", "Rose Thatcher",
           "Hugh Carter", "Ellen Shepherd", "Sam Fisher", "Jane Turner", "Ned Woods", "Lucy Weaver",
           "Owen Potter", "Grace Brewer", "Alf Tanner", "Ivy Chandler", "Ben Cartwright", "Meg Glover",
           "Walt Sawyer", "Iris Wright", "Jack Dyer", "Nell Hayward", "Rob Archer"]


def graves(d, slots, n, facing):
    for i, (x, y, z) in enumerate(slots[:n]):
        d.grave(x, y, z, facing, NAMES_G[i % len(NAMES_G)])


def tree(d, x, y, z, log, leaves, h, r=2, cone=False):
    for k in range(h):
        d.set(x, y + k, z, LOG(log))
    for k in range(r + 2):
        yy = y + h - 2 + k
        rr = max(0, r - k) if cone else (r if k < 2 else 1 if k == 2 else 0)
        for dx in range(-rr, rr + 1):
            for dz in range(-rr, rr + 1):
                if abs(dx) + abs(dz) > rr + (0 if cone else 1):
                    continue
                if d.bp.inside(x + dx, yy, z + dz) and d.air(x + dx, yy, z + dz):
                    d.set(x + dx, yy, z + dz, f"{leaves}[distance=1,persistent=true,waterlogged=false]")
    if d.air(x, y + h, z):
        d.set(x, y + h, z, f"{leaves}[distance=1,persistent=true,waterlogged=false]")


def gy_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (25, 20, 28))
    d.fill(1, 1, 1, 23, 1, 26, "grass_block[snowy=false]")
    # wall
    for x in range(1, 24):
        for z in range(1, 27):
            if x in (1, 23) or z in (1, 26):
                d.set(x, 2, z, "mossy_stone_brick_wall" if (x + z) % 3 == 0 else "stone_brick_wall")
    # lychgate
    gx = 12
    for x in range(gx - 1, gx + 2):
        d.set(x, 2, 1, AIR)
    for x in (gx - 2, gx + 2):
        for z in (0, 2):
            for y in range(2, 5):
                d.set(x, y, z, LOG("stripped_oak_log"))
    for x in range(gx - 3, gx + 4):
        d.set(x, 5, 0, ST("deepslate_tile", "south"))
        d.set(x, 6, 1, SL("deepslate_tile"))
        d.set(x, 5, 1, "oak_planks")
        d.set(x, 5, 2, ST("deepslate_tile", "north"))
    for z in (0, 2):
        d.set(gx - 2, 5, z, "oak_planks")
        d.set(gx + 2, 5, z, "oak_planks")
    d.set(gx - 1, 4, 1, LANT)
    d.set(gx + 1, 4, 1, LANT)
    d.chair(gx - 2, 2, 1, "west", "oak", sit=False)
    d.chair(gx + 2, 2, 1, "east", "oak", sit=False)
    for z in range(0, 19):
        for x in (gx - 1, gx, gx + 1):
            d.set(x, 1, z, "gravel")
    # chapel
    cx1, cz1, cx2, cz2 = 8, 18, 16, 25
    d.box(cx1, 2, cz1, cx2, 5, cz2, "stone_bricks", floor="stone_bricks")
    for x in range(cx1, cx2 + 1):
        for z in range(cz1, cz2 + 1):
            if (x in (cx1, cx2) or z in (cz1, cz2)) and (x * 3 + z) % 5 == 0:
                d.set(x, 2 + (x + z) % 4, z, "mossy_stone_bricks")
    soft(d, d.gable, cx1, cz1, cx2, cz2, 6, "z", "deepslate_tile_stairs", "deepslate_tile_slab", "stone_bricks", 1)
    d.door(gx, 2, cz1, "south", "oak")
    d.set(gx, 4, cz1, "chiseled_stone_bricks")
    d.set(gx, 8, cz1, "glass_pane")
    d.set(gx, 9, cz1, "glass_pane")
    for z in (20, 23):
        d.window(cx1, 3, z, cx1, 5, z)
        d.window(cx2, 3, z, cx2, 5, z)
    d.window(gx, 4, cz2, gx, 6, cz2, "red_stained_glass_pane")
    # altar, pews, vestry rack
    d.set(gx - 1, 2, cz2 - 1, "chiseled_stone_bricks")
    d.set(gx, 2, cz2 - 1, "chiseled_stone_bricks")
    d.set(gx + 1, 2, cz2 - 1, "chiseled_stone_bricks")
    d.candle(gx - 1, 3, cz2 - 1, 3)
    d.candle(gx + 1, 3, cz2 - 1, 3)
    d.set(gx, 3, cz2 - 1, "white_banner") if False else None
    d.rug(gx, cz1 + 1, gx, cz2 - 2, 2, ("red_carpet",), "plain")
    for z in (cz1 + 2, cz1 + 4):
        for x in (cx1 + 1, cx1 + 2, cx2 - 2, cx2 - 1):
            d.chair(x, 2, z, "north", "oak", sit=(z == cz1 + 2 and x in (cx1 + 2, cx2 - 2)))
    d.rack(cx1 + 1, 2, cz2 - 1, "east")
    d.hut(cx2 - 1, 2, cz2 - 1)
    for z in (cz1 + 2, cz2 - 2):
        d.set(gx, 5, z, LANT)
    # graves either side of the path
    slots = []
    for z in (5, 8, 11, 14):
        for x in (10, 14, 8, 16, 6, 18, 4, 20):
            slots.append((x, 2, z))
    graves(d, slots, d.req["yard"]["minecolonies:blockminecoloniesnamedgrave"], "north")
    for x, y, z in slots[:d.req["yard"]["minecolonies:blockminecoloniesnamedgrave"]]:
        if (x + z) % 3 == 0:
            d.set(x, 2, z + 1, "poppy")
        elif (x + z) % 3 == 1:
            d.set(x, 2, z + 1, "oxeye_daisy")
    if L >= 3:                                                    # bell-cote on the front gable
        for y in range(10, 13):
            d.set(gx - 1, y, cz1, "stone_bricks")
            d.set(gx + 1, y, cz1, "stone_bricks")
        d.set(gx, 12, cz1, "bell[attachment=ceiling,facing=north,powered=false]")
        d.set(gx, 13, cz1, "stone_brick_slab[type=bottom,waterlogged=false]")
        d.set(gx - 1, 13, cz1, "stone_brick_slab[type=bottom,waterlogged=false]")
        d.set(gx + 1, 13, cz1, "stone_brick_slab[type=bottom,waterlogged=false]")
    if L >= 4:                                                    # yews
        tree(d, 4, 2, 22, "dark_oak_log", "spruce_leaves", 4, 2)
        tree(d, 20, 2, 22, "dark_oak_log", "spruce_leaves", 4, 2)
    if L >= 5:
        for z in (4, 10, 16):
            for x in (gx - 2, gx + 2):
                d.set(x, 2, z, "stone_brick_wall")
                d.set(x, 3, z, LANT_S)
        d.chair(3, 2, 17, "east", "oak", sit=False)
        d.chair(21, 2, 17, "west", "oak", sit=False)
    return d


def gy_cascadia(rel, L):
    d = Design("Cascadia", rel, (29, 22, 23), paving="coarse_dirt")
    d.fill(1, 1, 1, 27, 1, 21, "grass_block[snowy=false]")
    for x in range(1, 28):
        for z in range(1, 22):
            if (x * 7 + z * 5) % 11 == 0:
                d.set(x, 1, z, "podzol[snowy=false]")
            if x in (1, 27) or z in (1, 21):
                d.set(x, 2, z, LOG("spruce_log") if (x + z) % 4 == 0 else "spruce_fence")
    # log gate arch
    gx = 16
    for x in range(gx - 1, gx + 2):
        d.set(x, 2, 1, AIR)
    for x in (gx - 2, gx + 2):
        for y in range(2, 7):
            d.set(x, y, 1, LOG("spruce_log"))
    for x in range(gx - 3, gx + 4):
        d.set(x, 7, 1, LOG("stripped_spruce_log", "x"))
    d.sign(gx, 6, 0, "north", ["PINE HILL", "CEMETERY"], "spruce")
    d.sign(gx, 6, 2, "south", ["REST IN", "PEACE"], "spruce")
    for z in range(0, 21):
        d.set(gx, 1, z, "coarse_dirt")
    # caretaker's chapel (log) on the west
    x1, z1, x2, z2 = 3, 6, 10, 13
    cs_walls(d, x1, z1, x2, z2, 2, 5)
    d.fill(x1 + 1, 1, z1 + 1, x2 - 1, 1, z2 - 1, "spruce_planks")
    cs_roof(d, x1, z1, x2, z2, 6, "z")
    for y in range(9, 12):
        d.set(6, y, z1 - 1, "spruce_fence" if y < 11 else "spruce_fence")
    d.set(7, 9, z1 - 1, "spruce_fence")
    d.set(5, 9, z1 - 1, "spruce_fence")
    d.door(6, 2, z1, "south", "spruce")
    d.window(8, 3, z1, 8, 4, z1)
    d.window(x2, 3, 9, x2, 4, 10)
    d.window(6, 3, z2, 7, 4, z2, "yellow_stained_glass_pane")
    cs_trim(d, x1, z1, x2, z2, 2, 5)
    # porch with bench
    for x in range(x1, x2 + 1):
        for z in (z1 - 2, z1 - 1):
            d.set(x, 1, z, "spruce_planks")
        d.set(x, 5, z1 - 2, ST("spruce", "south"))
        d.set(x, 5, z1 - 1, SL("spruce", "top"))
    for x in (x1, x2):
        for y in range(2, 5):
            d.set(x, y, z1 - 2, LOG("spruce_log"))
    d.chair(x1 + 1, 2, z1 - 1, "south", "spruce", sit=True)
    d.chair(x1 + 2, 2, z1 - 1, "south", "spruce", sit=True)
    d.lamp(6, 4, z1 - 1)
    for z in range(z1 - 1, 1, -1):
        d.set(6, 1, z, "coarse_dirt")
    for x in range(7, gx):
        d.set(x, 1, 3, "coarse_dirt")
    # inside: altar table, benches, rack
    d.set(6, 2, z2 - 1, "spruce_planks")
    d.set(7, 2, z2 - 1, "spruce_planks")
    d.candle(6, 3, z2 - 1, 2)
    d.candle(7, 3, z2 - 1, 1)
    for z in (z1 + 2, z1 + 4):
        d.chair(4, 2, z, "north", "spruce", sit=False)
        d.chair(5, 2, z, "north", "spruce", sit=False)
        d.chair(8, 2, z, "north", "spruce", sit=False)
        d.chair(9, 2, z, "north", "spruce", sit=False)
    d.rack(x2 - 1, 2, z1 + 1, "west")
    d.hut(x1 + 1, 2, z1 + 1)
    d.lamp(6, 5, 9)
    # graves in a grid on the east
    slots = []
    for z in (5, 8, 11, 14, 17):
        for x in (14, 18, 12, 20, 22, 24):
            slots.append((x, 2, z))
    n = d.req["yard"]["minecolonies:blockminecoloniesnamedgrave"]
    graves(d, slots, n, "north")
    for x, y, z in slots[:n]:
        if (x + z) % 2:
            d.set(x, 2, z + 1, "fern" if x % 4 else "lily_of_the_valley")
    for z in range(4, 20):
        d.set(gx, 1, z, "coarse_dirt")
    trees = [(25, 4), (4, 18), (9, 19), (25, 19), (12, 19), (19, 19)]
    for i, (x, z) in enumerate(trees[:1 + L]):
        tree(d, x, 2, z, "spruce_log", "spruce_leaves", 6 + i % 2, 2, cone=True)
    for z in (4, 10, 16):
        d.set(gx - 1, 2, z, "spruce_fence")
        d.set(gx - 1, 3, z, LANT_S)
    return d


def gy_neoterra(rel, L):
    d = Design("Neoterra", rel, (23, 14, 25), paving="smooth_stone")
    d.fill(1, 1, 1, 21, 1, 23, "grass_block[snowy=false]")
    for x in range(1, 22):
        for z in range(1, 24):
            if x in (1, 21) or z in (1, 23):
                d.set(x, 1, z, "smooth_stone")
                if not (z == 1 and 9 <= x <= 13):
                    d.set(x, 2, z, "white_concrete" if z == 1 else "birch_leaves[distance=1,persistent=true,waterlogged=false]")
    d.sign(8, 2, 0, "north", ["", "MEMORIAL", "GARDENS"], "birch", glow=True, color="light_gray") if False else None
    for x in (8, 14):
        d.set(x, 2, 1, "light_gray_concrete")
        d.set(x, 3, 1, "light_gray_concrete")
        d.set(x, 4, 1, "sea_lantern")
    d.sign(8, 3, 0, "north", ["MEMORIAL", "GARDENS"], "birch", glow=True, color="white")
    # central path and cross paths
    for z in range(0, 24):
        d.set(11, 1, z, "smooth_stone")
        d.set(10, 1, z, "polished_diorite")
        d.set(12, 1, z, "polished_diorite")
    # pavilion with columbarium wall at the back
    px1, pz1, px2, pz2 = 4, 16, 18, 22
    d.fill(px1, 1, pz1, px2, 1, pz2, "polished_diorite")
    for x in range(px1, px2 + 1):
        for y in range(2, 6):
            d.set(x, y, pz2, "light_gray_concrete" if (x + y) % 2 else "smooth_quartz")
    for z in range(pz1, pz2 + 1):
        for x in (px1, px2):
            for y in range(2, 6):
                d.set(x, y, z, "white_concrete" if z in (pz1, pz2) else "light_gray_stained_glass_pane")
    d.fill(px1 - 1, 6, pz1 - 1, px2 + 1, 6, pz2, "smooth_quartz")
    for x in range(px1 - 1, px2 + 2):
        d.set(x, 6, pz1 - 1, "smooth_quartz_slab[type=bottom,waterlogged=false]")
    for x in range(px1 + 2, px2 - 1, 3):
        d.set(x, 5, 19, "sea_lantern") if False else None
    d.fill(px1 + 1, 5, pz1 + 2, px2 - 1, 5, pz1 + 2, "sea_lantern") if False else None
    for x in range(px1 + 2, px2 - 1, 4):
        d.set(x, 5, pz1 + 3, "end_rod[facing=down]")
    # reflecting pool and benches
    for x in range(7, 16):
        for z in (pz1 + 1, pz1 + 2):
            if x not in (10, 11, 12):
                d.set(x, 1, z, "water[level=0]")
    d.chair(9, 2, pz1 + 4, "south", "birch", sit=True)
    d.chair(13, 2, pz1 + 4, "south", "birch", sit=True)
    d.chair(8, 2, pz1 + 4, "south", "birch", sit=False)
    d.chair(14, 2, pz1 + 4, "south", "birch", sit=False)
    d.set(11, 2, pz2 - 1, "smooth_quartz")
    d.set(11, 3, pz2 - 1, "white_candle[candles=3,lit=false,waterlogged=false]")
    d.set(10, 2, pz2 - 1, "potted_white_tulip")
    d.set(12, 2, pz2 - 1, "potted_lily_of_the_valley")
    d.rack(px1 + 1, 2, pz2 - 1, "east")
    d.hut(px2 - 1, 2, pz2 - 1)
    # graves on the lawns
    slots = []
    for z in (4, 7, 10, 13):
        for x in (8, 14, 6, 16, 4, 18):
            slots.append((x, 2, z))
    n = d.req["yard"]["minecolonies:blockminecoloniesnamedgrave"]
    graves(d, slots, n, "north")
    for z in (5, 8, 11, 14):
        for x in range(3, 20):
            if x not in (10, 11, 12):
                d.set(x, 1, z, "smooth_stone_slab[type=double,waterlogged=false]" if False else "smooth_stone")
    for i, (x, z) in enumerate([(3, 3), (19, 3), (3, 15), (19, 15), (3, 9), (19, 9)][:1 + L]):
        tree(d, x, 2, z, "birch_log", "birch_leaves", 4, 1)
    for z in (4, 9, 14):
        for x in (9, 13):
            d.set(x, 2, z, "end_rod[facing=up]") if False else None
            d.set(x, 2, z, "white_concrete") if False else None
    for z in (3, 9, 15):
        d.set(9, 2, z, "white_concrete_powder") if False else None
        d.set(9, 2, z, "end_rod[facing=up]")
        d.set(13, 2, z, "end_rod[facing=up]")
    return d


@design("graveyard")
def graveyard(pack, rel, L):
    return tidy({"Hearthwood": gy_hearthwood, "Cascadia": gy_cascadia, "Neoterra": gy_neoterra}[pack](rel, L))


# ================================================================================================ MYSTICAL SITE
"""
Mystical site
  Hearthwood  Stone circle on a village green: a ring of standing stones round an altar stone with candles,
              eight benches facing in, a holy well (L2+), lintels turning the stones into trilithons (L3+),
              a hawthorn and flower meadow (L4+), lanterns (L5).
  Cascadia    Sacred spring: a mossy rock outcrop with a waterfall into a pool, an open log pavilion with a
              hip roof beside it, log benches round a fire pit, cairns and spruces that multiply with level.
  Neoterra    Crystal plaza: a round quartz plaza with an amethyst crystal on a plinth in a ring of water,
              white pylons with light rods, benches facing the crystal, a floating canopy ring (L3+).
"""


def ms_hearthwood(rel, L):
    d = Design("Hearthwood", rel, (23, 12, 23))
    c = 11
    for x in range(1, 22):
        for z in range(1, 22):
            r = ((x - c) ** 2 + (z - c) ** 2) ** 0.5
            d.set(x, 1, z, "grass_block[snowy=false]" if r > 2.5 else "moss_block")
    for z in range(0, 5):
        d.set(c, 1, z, "gravel")
    stones = []
    import math
    n = 12
    for i in range(n):
        a = 2 * math.pi * i / n
        x = round(c + 7 * math.sin(a))
        z = round(c - 7 * math.cos(a))
        stones.append((x, z))
    for i, (x, z) in enumerate(stones):
        if i == 0:
            continue                                              # entrance gap on the street side
        h = 3 + (i % 2)
        for y in range(2, 2 + h):
            d.set(x, y, z, ["stone", "andesite", "mossy_cobblestone", "cobblestone"][(i + y) % 4]
                  if y < 2 + h - 1 else "stone")
    if L >= 3:                                                    # lintels on pairs
        for i in range(1, n - 1, 2):
            (ax, az), (bx, bz) = stones[i], stones[i + 1]
            for x, z in ((ax, az), (bx, bz)):
                for y in range(2, 6):
                    d.set(x, y, z, "stone" if y != 3 else "mossy_cobblestone")
            steps = max(abs(bx - ax), abs(bz - az))
            for k in range(steps + 1):
                d.set(round(ax + (bx - ax) * k / steps), 6, round(az + (bz - az) * k / steps), "stone")
    # altar
    d.set(c, 2, c, "chiseled_stone_bricks")
    d.set(c - 1, 2, c, "stone_brick_slab[type=top,waterlogged=false]")
    d.set(c + 1, 2, c, "stone_brick_slab[type=top,waterlogged=false]")
    d.candle(c - 1, 3, c, 3)
    d.candle(c + 1, 3, c, 2)
    d.set(c, 3, c, "potted_flowering_azalea_bush")
    d.hut(c, 2, c + 2)
    # benches facing in
    for x, z, back in ((c - 3, c - 3, "north"), (c + 3, c - 3, "north"), (c - 3, c + 3, "south"),
                       (c + 3, c + 3, "south")):
        d.chair(x, 2, z, back, "oak")
        d.chair(x + (1 if x < c else -1), 2, z, back, "oak")
    if L >= 2:                                                    # holy well
        wx, wz = 18, 18
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                d.set(wx + dx, 2, wz + dz, "stone_bricks" if (dx, dz) != (0, 0) else "water[level=0]")
        d.set(wx, 1, wz, "water[level=0]")
        for dx, dz in ((-1, -1), (1, 1)):
            for y in (3, 4):
                d.set(wx + dx, y, wz + dz, "oak_fence")
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                d.set(wx + dx, 5, wz + dz, SL("dark_oak"))
        d.set(wx, 4, wz, "chain[axis=y,waterlogged=false]")
    if L >= 4:
        tree(d, 4, 2, 4, "oak_log", "flowering_azalea_leaves", 3, 2)
        tree(d, 18, 2, 4, "oak_log", "flowering_azalea_leaves", 3, 2)
        for x, z in ((3, 16), (5, 19), (7, 20), (15, 3), (2, 10), (20, 11)):
            d.set(x, 2, z, "cornflower" if x % 2 else "poppy")
    if L >= 5:
        for x, z in ((c - 1, 2), (c + 1, 2)):
            d.set(x, 2, z, "oak_fence")
            d.set(x, 3, z, LANT_S)
    return d


def ms_cascadia(rel, L):
    d = Design("Cascadia", rel, (25, 16, 25), paving="coarse_dirt")
    for x in range(1, 24):
        for z in range(1, 24):
            d.set(x, 1, z, "podzol[snowy=false]" if (x * 5 + z * 3) % 7 == 0 else "grass_block[snowy=false]")
    for z in range(0, 9):
        d.set(12, 1, z, "coarse_dirt")
        d.set(11, 1, z, "coarse_dirt")
    # rock outcrop with waterfall into a pool (south)
    for x in range(6, 19):
        for z in range(18, 24):
            hgt = 6 - abs(x - 12) // 2 - (23 - z) // 2
            for y in range(2, 2 + max(1, hgt)):
                d.set(x, y, z, "mossy_cobblestone" if (x + y + z) % 3 == 0 else
                      ("tuff" if (x + z) % 4 == 0 else "andesite"))
            d.set(x, 2 + max(1, hgt), z, "moss_block")
    for x in range(9, 16):
        for z in range(13, 18):
            if abs(x - 12) + abs(z - 15) <= 4:
                d.set(x, 1, z, "water[level=0]")
                d.set(x, 0, z, "gravel") if False else None
    for y in range(2, 6):
        d.set(12, y, 18, "water[level=0]")
    d.set(12, 6, 18, "water[level=0]")
    for x in (11, 13):
        d.set(x, 1, 13, "mossy_cobblestone")
    # fire pit and log benches (8 seats)
    fx, fz = 12, 9
    d.set(fx, 1, fz, "cobblestone")
    d.set(fx, 2, fz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for x, z, back in ((fx - 3, fz, "west"), (fx + 3, fz, "east")):
        for dz in (-1, 0, 1):
            d.chair(x, 2, z + dz, back, "spruce")
    d.chair(fx - 1, 2, fz - 3, "north", "spruce")
    d.chair(fx + 1, 2, fz - 3, "north", "spruce")
    d.hut(fx, 2, fz - 3)
    # open log pavilion (east)
    px1, pz1, px2, pz2 = 17, 5, 21, 11
    for x in range(px1, px2 + 1):
        for z in range(pz1, pz2 + 1):
            d.set(x, 1, z, "spruce_planks")
    for x, z in ((px1, pz1), (px2, pz1), (px1, pz2), (px2, pz2), (px1, 8), (px2, 8)):
        d.set(x, 1, z, "cobblestone")
        for y in range(2, 5):
            d.set(x, y, z, LOG("spruce_log"))
    for x in range(px1, px2 + 1):
        for z in (pz1, pz2):
            d.set(x, 5, z, LOG("stripped_spruce_log", "x"))
    for z in range(pz1, pz2 + 1):
        for x in (px1, px2):
            d.set(x, 5, z, LOG("stripped_spruce_log", "z"))
    soft(d, d.hip, px1, pz1, px2, pz2, 6, "deepslate_tile_stairs", "deepslate_tile_slab", 1)
    d.set(19, 5, 8, LANT)
    d.set(19, 2, 10, "spruce_planks")
    d.candle(19, 3, 10, 4)
    d.set(19, 2, 6, "decorated_pot[cracked=false,facing=north,waterlogged=false]")
    # cairns
    cairns = [(4, 5), (4, 13), (20, 15), (7, 16), (3, 9)]
    for i, (x, z) in enumerate(cairns[:L]):
        d.set(x, 2, z, "cobblestone")
        d.set(x, 3, z, "mossy_cobblestone")
        d.set(x, 4, z, "cobblestone_wall")
    trees = [(2, 20), (22, 20), (2, 2), (22, 2), (6, 22), (18, 22)]
    for i, (x, z) in enumerate(trees[:1 + L]):
        tree(d, x, 2, z, "spruce_log", "spruce_leaves", 6, 2, cone=True)
    return d


def ms_neoterra(rel, L):
    d = Design("Neoterra", rel, (21, 14, 21), paving="smooth_stone")
    c = 10
    for x in range(0, 21):
        for z in range(0, 21):
            r = ((x - c) ** 2 + (z - c) ** 2) ** 0.5
            if r <= 9.3:
                d.set(x, 1, z, "smooth_quartz" if r > 3.5 else "polished_diorite")
                if 2.0 <= r < 3.0:
                    d.set(x, 1, z, "water[level=0]")
                if 8.5 <= r <= 9.3 and z > 2:
                    d.set(x, 1, z, "moss_block")
                    if (x + z) % 3 == 0:
                        d.set(x, 2, z, "azalea")
            else:
                d.set(x, 1, z, "grass_block[snowy=false]")
    # crystal plinth
    d.set(c, 2, c, "smooth_quartz")
    d.set(c, 3, c, "amethyst_block")
    d.set(c, 4, c, "budding_amethyst")
    d.set(c, 5, c, "amethyst_cluster[facing=up,waterlogged=false]")
    for dx, dz, f in ((1, 0, "east"), (-1, 0, "west"), (0, 1, "south"), (0, -1, "north")):
        d.set(c + dx, 2, c + dz, "amethyst_block")
        d.set(c + dx, 3, c + dz, f"amethyst_cluster[facing=up,waterlogged=false]")
    # pylons
    import math
    for i in range(8):
        a = 2 * math.pi * (i + 0.5) / 8
        x = round(c + 7 * math.sin(a))
        z = round(c - 7 * math.cos(a))
        for y in range(2, 5):
            d.set(x, y, z, "white_concrete" if y < 4 else "sea_lantern")
        d.set(x, 5, z, ENDROD())
    # benches facing the crystal (8 seats)
    for x, z, back in ((c - 5, c - 1, "west"), (c - 5, c + 1, "west"), (c + 5, c - 1, "east"), (c + 5, c + 1, "east"),
                       (c - 1, c + 5, "south"), (c + 1, c + 5, "south"), (c - 2, c + 5, "south"), (c + 2, c + 5, "south")):
        d.chair(x, 2, z, back, "birch")
    d.hut(c, 2, c - 5)
    if L >= 2:
        for x, z in ((c - 5, c), (c + 5, c), (c, c + 5)):
            d.set(x, 2, z, SL("smooth_quartz", "top"))
    if L >= 3:                                                    # floating canopy ring on the pylons
        for x in range(0, 21):
            for z in range(0, 21):
                r = ((x - c) ** 2 + (z - c) ** 2) ** 0.5
                if 6.5 <= r < 8.0 and d.air(x, 6, z):
                    d.set(x, 6, z, "white_stained_glass" if (x + z) % 2 else "smooth_quartz_slab[type=bottom,waterlogged=false]")
    if L >= 4:
        for x, z in ((c, c - 3), (c, c + 3), (c - 3, c), (c + 3, c)):
            d.set(x, 1, z, "sea_lantern")
    if L >= 5:
        for y in range(6, 9):
            d.set(c, y, c, "end_rod[facing=up]") if False else None
        d.set(c, 6, c, "end_rod[facing=up]")
    return d


@design("mysticalsite")
def mysticalsite(pack, rel, L):
    return tidy({"Hearthwood": ms_hearthwood, "Cascadia": ms_cascadia, "Neoterra": ms_neoterra}[pack](rel, L))
