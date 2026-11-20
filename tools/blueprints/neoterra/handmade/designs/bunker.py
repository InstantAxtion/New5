"""
Bunker (underground shelter, ground surface at y = 24) and its four child rooms
(bunkerkitchen / bunkerclinic / bunkerschool / bunkerfarm).

Two underground decks under every pack:  deck A (living, floor y18, 3 high) and deck B (stores & plant, floor y13,
4 high). The child rooms are carved and walled by the parent; each child blueprint is exactly the room's floor +
air + ceiling box (no walls), so it slots into the reserved space.

  Neoterra   "Civil Defence Shelter 07": a chunky concrete blast-door portal with hazard-striped frame and a
             sliding blast door parked beside it, grass berm, vent stacks; a long straight ramp stair down to a
             reception hall and a concrete spine corridor (cyan stripe, flush sea-lantern ceiling). Deck A: rec room,
             ops room + decon washroom, mess kitchen, infirmary, classroom, dormitory. Deck B (concrete stair core):
             archive, barrel vault, workshop, generator hall with a ventilation duct to the surface, hydroponic grow
             room + ration store (L2+). L3 solar field, L4 guard booth + fence, L5 radio mast.
  Hearthwood "The Undercroft": a ruined chapel in a cottage garden; a pointed arch over worn steps leads down to
             vaulted stone-brick galleries (springers, dark-oak beams, lanterns). The garden well is the air shaft.
             Deck A: snug, dormitory, infirmary, kitchen, schoolroom, laundry/still-room, map room. Deck B: muniment
             archive, cellar vault of casks, smithy, boiler room, lamp-lit cellar garden + root store (L2+).
  Cascadia   "Ridge Refuge": a mine adit with a timber portal set into a mossy rock knoll with spruces; rails run
             out to a blacksmith's lean-to (the workshop) at the foot of the rock face. Inside: timbered drifts,
             rough rock walls. Deck A: mess hall, cookhouse, sick bay, bunkhouse. Deck B: archive, powder-magazine
             style barrel vault, boiler/vent room with a stack up through the knoll, schoolroom, grow cave + root
             cellar (L2+). L3 ore chute & lamp posts, L5 lookout on the knoll.
"""
from __future__ import annotations

from types import SimpleNamespace as NS

from hm import Design, design, AIR, D4, OPP, CW, SOLID, KEEP

GY = 24
SW = GY + 1                                  # surface walk level
LV = {"A": (18, 21), "B": (13, 17)}          # deck -> (floor y, top air y); ceiling = top + 1
CHILD_PATH = {"kitchen": "fundamentals/bunkerkitchen0.blueprint", "clinic": "fundamentals/bunkerclinic0.blueprint",
              "school": "fundamentals/bunkerschool0.blueprint", "farm": "fundamentals/bunkerfarm0.blueprint"}
CHILD_KINDS = set(CHILD_PATH)


def H(x, y, z, salt=0):
    """Deterministic hash in 0..99."""
    return ((x * 73856093) ^ (y * 19349663) ^ (z * 83492791) ^ (salt * 2654435761)) % 100


# ---------------------------------------------------------------------------------------------------- plans
# The underground street grid (base coordinates, 55 x 55) shared by the packs; each pack transforms it (mirror /
# offset) and adds its own surface. Deck A = living deck, deck B = stores & plant (reached by a stair core).
# space: (kind, deck, x1, z1, x2, z2, minL)  interior box, walls one block outside; corridors are kind corr / hall.
# extra door: (x, z, deck, minL, kind)  'door' / 'open' / 'vault'.  Room doors onto corridors are found
# automatically (one per room, first adjacent corridor in list order).
BASE = dict(
    ramp=(26, 3, 5),
    hut=(22, 19, 14),
    wells=[(30, 28, "A", "B", 2, +1)],          # lane-1 x, z0, upper deck, lower deck, minL, lane-2 side
    spaces=[
        # ---- deck A
        ("hall", "A", 22, 11, 32, 14, 1),
        ("corr", "A", 26, 15, 28, 33, 1),
        ("corr", "A", 2, 24, 25, 26, 1),
        ("corr", "A", 29, 24, 40, 26, 1),
        ("corr", "A", 41, 24, 52, 26, 2),
        ("corr", "A", 26, 34, 28, 52, 4),
        ("corr", "A", 2, 42, 52, 44, 4),
        ("vault", "A", 13, 1, 23, 9, 1),
        ("archive", "A", 31, 1, 42, 9, 1),
        ("radio", "A", 44, 1, 52, 9, 5),
        ("clinic", "A", 2, 16, 12, 22, 1),
        ("kitchen", "A", 14, 16, 24, 22, 1),
        ("dorm", "A", 30, 16, 40, 22, 1),
        ("mess", "A", 42, 16, 52, 22, 2),
        ("school", "A", 2, 28, 12, 34, 1),
        ("common", "A", 14, 28, 24, 34, 1),
        ("workroom", "A", 33, 28, 40, 34, 1),
        ("ops", "A", 42, 28, 52, 34, 3),
        ("laundry", "A", 2, 36, 12, 40, 4),
        ("lab", "A", 14, 36, 24, 40, 4),
        ("gym", "A", 30, 36, 40, 40, 4),
        ("office", "A", 42, 36, 52, 40, 5),
        ("chapel", "A", 2, 46, 12, 52, 4),
        ("bunks", "A", 14, 46, 24, 52, 5),
        ("store", "A", 30, 46, 40, 52, 5),
        ("canteen", "A", 42, 46, 52, 52, 5),
        # ---- deck B
        ("corr", "B", 2, 24, 52, 26, 2),
        ("corr", "B", 26, 2, 28, 23, 3),
        ("corr", "B", 26, 27, 28, 52, 4),
        ("fabrication", "B", 2, 16, 12, 22, 3),
        ("generator", "B", 14, 16, 24, 22, 2),
        ("farm", "B", 30, 16, 40, 22, 2),
        ("pantry", "B", 42, 16, 52, 22, 2),
        ("water", "B", 2, 2, 12, 14, 4),
        ("vault", "B", 14, 2, 24, 14, 3),
        ("records", "B", 30, 2, 40, 14, 3),
        ("power", "B", 42, 2, 52, 14, 4),
        ("armory", "B", 2, 28, 12, 34, 4),
        ("store", "B", 14, 28, 24, 34, 4),
        ("cistern", "B", 34, 28, 40, 34, 5),
        ("server", "B", 42, 28, 52, 34, 5),
        ("reactor", "B", 2, 36, 12, 44, 5),
        ("turbine", "B", 14, 36, 24, 44, 5),
        ("hydro", "B", 30, 36, 40, 44, 5),
        ("bunks", "B", 42, 36, 52, 44, 5),
    ],
    doors=[(43, 5, "A", 5, "door"), (7, 15, "B", 4, "door"), (47, 15, "B", 4, "door"),
           (13, 40, "B", 5, "door"), (41, 40, "B", 5, "door"),
           (29, 28, "A", 2, "open"), (31, 27, "B", 2, "open")],
    child_huts={"kitchen": (24, 16), "clinic": (12, 16), "school": (2, 34), "farm": (30, 16)},
)


def _transform(base, sx, mirror=False, dz=0):
    W = 55

    def X(x):
        return W - 1 - x if mirror else x

    def rect(x1, x2):
        a, b = X(x1), X(x2)
        return min(a, b), max(a, b)
    P = {}
    rx, rw, rz = base["ramp"]
    a, _ = rect(rx, rx + rw - 1)
    P["ramp"] = (a, rw, rz + dz)
    hx, hy, hz = base["hut"]
    P["hut"] = (X(hx), hy, hz + dz)
    P["wells"] = [(X(x), z + dz, u, l, ml, -s if mirror else s) for (x, z, u, l, ml, s) in base["wells"]]
    P["spaces"] = []
    for (k, dk, x1, z1, x2, z2, ml) in base["spaces"]:
        a, b = rect(x1, x2)
        P["spaces"].append((k, dk, a, z1 + dz, b, z2 + dz, ml))
    P["doors"] = [(X(x), z + dz, dk, ml, k) for (x, z, dk, ml, k) in base["doors"]]
    P["child_huts"] = {k: (X(x), z + dz) for k, (x, z) in base["child_huts"].items()}
    return P


PLANS = {
    "Neoterra": dict(size=(55, 52, 55), **_transform(BASE, 55)),
    "Hearthwood": dict(size=(61, 52, 55), **_transform(BASE, 61, mirror=True)),
    "Cascadia": dict(size=(55, 52, 61), **_transform(BASE, 55, dz=6)),
}

MATS = {
    "Neoterra": dict(wood="birch", door="birch", step="polished_andesite_stairs", solid="polished_andesite",
                     ceil="white_concrete", light="flush", lightblock="sea_lantern",
                     floor={"corr": "polished_andesite", "hall": "polished_diorite", "vault": "smooth_stone",
                            "generator": "gray_concrete", "workshop": "smooth_stone", "pantry": "smooth_stone",
                            "wash": "white_concrete", "default": "polished_diorite"},
                     child_floor={"kitchen": "white_concrete", "clinic": "white_concrete",
                                  "school": "birch_planks", "farm": "smooth_stone"},
                     bed="cyan", rug="cyan_carpet", rug2="light_gray_carpet", counter="smooth_quartz",
                     slab="smooth_quartz_slab", plant="potted_bamboo"),
    "Hearthwood": dict(wood="dark_oak", door="dark_oak", step="stone_brick_stairs", solid="stone_bricks",
                       ceil="stone_bricks", light="hang", lightblock="lantern",
                       floor={"corr": "stone_bricks", "vault": "cobblestone", "generator": "bricks",
                              "workshop": "cobblestone", "pantry": "cobblestone", "wash": "bricks",
                              "default": "spruce_planks"},
                       child_floor={"kitchen": "bricks", "clinic": "oak_planks", "school": "oak_planks",
                                    "farm": "coarse_dirt"},
                       bed="red", rug="red_carpet", rug2="brown_carpet", counter="dark_oak_planks",
                       slab="dark_oak_slab", plant="potted_red_tulip"),
    "Cascadia": dict(wood="spruce", door="spruce", step="spruce_stairs", solid="spruce_planks",
                     ceil="spruce_planks", light="hang", lightblock="lantern",
                     floor={"corr": "packed_mud", "vault": "stone", "generator": "cobblestone",
                            "pantry": "coarse_dirt", "default": "spruce_planks"},
                     child_floor={"kitchen": "spruce_planks", "clinic": "spruce_planks", "school": "spruce_planks",
                                  "farm": "coarse_dirt"},
                     bed="brown", rug="brown_carpet", rug2="green_carpet", counter="stripped_spruce_wood",
                     slab="spruce_slab", plant="potted_fern"),
}


def wall_block(pack, x, y, z, floor_y):
    h = H(x, y, z)
    if pack == "Neoterra":
        return "gray_concrete" if y == floor_y else "light_gray_concrete"
    if pack == "Hearthwood":
        if y == floor_y:
            return "polished_andesite"
        return "mossy_stone_bricks" if h < 16 else "stone_bricks"
    return ("tuff" if h < 22 else "andesite" if h < 44 else "cobblestone" if h < 58
            else "mossy_cobblestone" if h < 64 else "stone")


def st(name, facing, half="bottom", shape="straight"):
    return f"{name}[facing={facing},half={half},shape={shape},waterlogged=false]"


def slab(name, t="top"):
    return f"{name}[type={t},waterlogged=false]"


def trap(wood, facing, half="top", open_=False):
    return f"{wood}_trapdoor[facing={facing},half={half},open={'true' if open_ else 'false'},powered=false," \
           f"waterlogged=false]"


def chiseled(facing, k):
    s = ",".join(f"slot_{i}_occupied={'true' if (k * 7 + i * 3) % 5 < 3 else 'false'}" for i in range(6))
    return f"chiseled_bookshelf[facing={facing},{s}]"


# ---------------------------------------------------------------------------------------------------- rooms
def room(x1, z1, x2, z2, y, top, keep=()):
    return NS(x1=x1, z1=z1, x2=x2, z2=z2, y=y, top=top, keep=set(keep), W=x2 - x1 + 1, D=z2 - z1 + 1)


def wallcells(R, side):
    if side == "north":
        return [(x, R.z1) for x in range(R.x1, R.x2 + 1)]
    if side == "south":
        return [(x, R.z2) for x in range(R.x1, R.x2 + 1)]
    if side == "west":
        return [(R.x1, z) for z in range(R.z1, R.z2 + 1)]
    return [(R.x2, z) for z in range(R.z1, R.z2 + 1)]


INTO = {"north": "south", "south": "north", "west": "east", "east": "west"}


def door_sides(R):
    s = set()
    for (x, z) in R.keep:
        if z == R.z1:
            s.add("north")
        if z == R.z2:
            s.add("south")
        if x == R.x1:
            s.add("west")
        if x == R.x2:
            s.add("east")
    return s


class Frame:
    """Room-local frame: u runs along the 'front' wall, v away from it (v = 0 is the row next to the front)."""

    def __init__(self, R, front):
        self.R, self.front = R, front
        if front in ("north", "south"):
            self.U, self.V = R.W, R.D
        else:
            self.U, self.V = R.D, R.W
        a, b = self.xz(0, 0), self.xz(1, 0) if self.U > 1 else self.xz(0, 0)
        du = (b[0] - a[0], b[1] - a[1])
        self.right = next((k for k, v in D4.items() if v == du), CW[front])
        self.left = OPP[self.right]
        self.back = OPP[front]

    def xz(self, u, v):
        R = self.R
        if self.front == "north":
            return R.x1 + u, R.z1 + v
        if self.front == "south":
            return R.x2 - u, R.z2 - v
        if self.front == "west":
            return R.x1 + v, R.z2 - u
        return R.x2 - v, R.z1 + u

    def uv(self, x, z):
        for u in range(self.U):
            for v in range(self.V):
                if self.xz(u, v) == (x, z):
                    return u, v
        return None


def mark_keep(d, R, on=True):
    for (x, z) in R.keep:
        if on:
            if d.air(x, R.y, z):
                d.set(x, R.y, z, "barrier")
        elif d.get(x, R.y, z) == "minecraft:barrier":
            d.set(x, R.y, z, AIR)


def free(d, R, x, z, h=1):
    return (x, z) not in R.keep and all(d.air(x, R.y + k, z) for k in range(h))


def flush_ok(d, x, y, z):
    """A flush ceiling light only where the ceiling is ours and nothing walks on top of it."""
    if not d.bp.inside(x, y, z):
        return False
    here = d.get(x, y, z)
    if here == AIR or "substitution" in here or not d.bp.inside(x, y + 1, z):
        return False
    above = d.get(x, y + 1, z)
    return above != AIR and "blocksubstitution" not in above


def lights(d, R, M, ceil_y, step=4, skip=()):
    """Ceiling lights on a grid: flush light blocks in the ceiling (if it is ours) or hanging lanterns."""
    xs = list(range(R.x1 + (R.W % step) // 2 + 1, R.x2, step)) or [(R.x1 + R.x2) // 2]
    zs = list(range(R.z1 + (R.D % step) // 2 + 1, R.z2, step)) or [(R.z1 + R.z2) // 2]
    if R.W <= 3:
        xs = [(R.x1 + R.x2) // 2]
    if R.D <= 3:
        zs = [(R.z1 + R.z2) // 2]
    for x in xs:
        for z in zs:
            if (x, z) in skip:
                continue
            if M["light"] == "flush":
                if flush_ok(d, x, ceil_y, z):
                    d.set(x, ceil_y, z, M["lightblock"])
                elif d.air(x, R.top, z):
                    d.set(x, R.top, z, "end_rod[facing=down]")
            elif d.air(x, R.top, z):
                d.lamp(x, R.top, z, "lantern")


# ---------------------------------------------------------------------------------------------------- furnishers
def f_dorm(d, R, M, L, n, sides=None):
    sides = sides or (["north", "south"] if R.W >= R.D else ["west", "east"])
    placed = []
    for side in sides:
        last = -9
        for i, (x, z) in enumerate(wallcells(R, side)):
            if len(placed) >= n:
                break
            dx, dz = D4[INTO[side]]
            fx, fz = x + dx, z + dz
            if i - last < 2 or not (free(d, R, x, z) and free(d, R, fx, fz)):
                continue
            if (x, z) in [(px + 0, pz) for px, pz, _ in placed]:
                continue
            d.bed(x, R.y, z, side, M["bed"])
            placed.append((x, z, side))
            last = i
    # nightstands between neighbouring beds and footlockers
    for x, z, side in placed:
        for s in (CW[side], OPP[CW[side]]):
            ox, oz = D4[s]
            nx, nz = x + ox, z + oz
            if R.x1 <= nx <= R.x2 and R.z1 <= nz <= R.z2 and free(d, R, nx, nz):
                d.set(nx, R.y, nz, slab(M["slab"]))
                d.set(nx, R.y + 1, nz, "lantern[hanging=false,waterlogged=false]" if (nx + nz) % 2
                      else "candle[candles=2,lit=false,waterlogged=false]")
                break
    return len(placed)


def sofa_row(d, R, M, side, n, sit=True):
    """Row of seats with backs to `side` wall, centred; returns seats placed."""
    cells = [c for c in wallcells(R, side) if free(d, R, *c)]
    k = 0
    if len(cells) > n:
        off = (len(cells) - n) // 2
        cells = cells[off:off + n]
    for (x, z) in cells:
        d.chair(x, R.y, z, side, M["wood"], sit=sit)
        k += 1
    return k


def f_common(d, R, M, L, pack, seats=10, maps=False):
    sides = door_sides(R)
    far = next(s for s in ("north", "west", "south", "east") if s not in sides)
    F = Frame(R, far)
    # feature wall at the front: screen / dartboard / notice board
    mid = F.U // 2
    # jukeboxes in the front corners
    for u in (0, F.U - 1):
        x, z = F.xz(u, 0)
        if free(d, R, x, z):
            d.item(x, R.y, z, "jukebox")
    got = 0
    # sofa facing the front wall, two rows back, with a low table in between
    for u in range(max(1, mid - 2), min(F.U - 1, mid + 3)):
        x, z = F.xz(u, 0)
        if free(d, R, x, z):
            if pack == "Neoterra":
                d.set(x, R.y, z, "smooth_quartz_slab[type=bottom,waterlogged=false]")
                d.set(x, R.y + 1, z, "black_stained_glass_pane" if u != mid else "black_stained_glass_pane")
            elif pack == "Hearthwood":
                d.set(x, R.y, z, f"{M['wood']}_planks" if u % 2 else "bookshelf")
                d.set(x, R.y + 1, z, "potted_red_tulip" if u == mid else "candle[candles=3,lit=false,waterlogged=false]")
            else:
                d.set(x, R.y, z, "spruce_planks")
                d.set(x, R.y + 1, z, "potted_fern" if u % 2 else "lantern[hanging=false,waterlogged=false]")
    if pack == "Hearthwood":
        x, z = F.xz(mid, 0)
        d.set(x, R.y + 2, z, "target[power=0]")          # dartboard
    if pack == "Cascadia":
        x, z = F.xz(mid, 0)
        d.set(x, R.y + 2, z, "brown_wall_banner[facing=%s]" % F.back)
    if F.V >= 6:
        for u in range(max(1, mid - 2), min(F.U - 1, mid + 3)):
            x, z = F.xz(u, 3)
            if free(d, R, x, z):
                d.chair(x, R.y, z, F.front, M["wood"])
                got += 1
            x, z = F.xz(u, 2)
            if free(d, R, x, z) and u in (mid - 1, mid, mid + 1):
                d.set(x, R.y, z, M["rug"])
    if maps:
        for u in (0, F.U - 1):
            x, z = F.xz(u, 1)
            if free(d, R, x, z):
                d.item(x, R.y, z, "cartography_table")
    mark_keep(d, R)
    # card tables in the remaining floor
    v0 = 5 if F.V >= 8 else 4
    rest = seats - got
    for v in range(v0, F.V - 1, 3):
        for u in range(1, F.U - 1, 3):
            if rest <= 0:
                break
            cells = [F.xz(u + a, v + b) for a in (-1, 0, 1) for b in (-1, 0, 1)]
            if not all(R.x1 <= cx <= R.x2 and R.z1 <= cz <= R.z2 and free(d, R, cx, cz) for cx, cz in cells):
                continue
            cx, cz = F.xz(u, v)
            d.table(cx, R.y, cz, M["wood"], "post")
            for s, (dx, dz) in D4.items():
                if rest <= 0:
                    break
                d.chair(cx + dx, R.y, cz + dz, s, M["wood"])
                rest -= 1
    # leftovers: benches along the side walls
    for side in (F.left, F.right):
        for (x, z) in wallcells(R, side):
            if rest <= 0:
                break
            uv = F.uv(x, z)
            if uv and uv[1] >= 2 and free(d, R, x, z):
                d.chair(x, R.y, z, side, M["wood"])
                rest -= 1
    mark_keep(d, R, False)
    if rest > 0:
        raise RuntimeError(f"common room short of {rest} seats")


def f_command(d, R, M, L, pack):
    sides = door_sides(R)
    F = Frame(R, next(s for s in ("north", "east", "west", "south") if s not in sides))
    mid = F.U // 2
    # consoles along the front wall
    for u in range(F.U):
        x, z = F.xz(u, 0)
        if not free(d, R, x, z):
            continue
        if pack == "Neoterra":
            d.set(x, R.y, z, "polished_andesite" if u % 3 else "observer[facing=%s,powered=false]" % F.back)
            d.set(x, R.y + 1, z, "black_stained_glass" if u % 2 else "redstone_lamp[lit=true]")
        else:
            d.set(x, R.y, z, f"{M['wood']}_planks")
            d.set(x, R.y + 1, z, "bookshelf" if u % 2 else f"{M['wood']}_planks")
    # chairs at the consoles
    for u in range(1, F.U - 1, 2):
        x, z = F.xz(u, 1)
        if free(d, R, x, z):
            d.chair(x, R.y, z, F.back, M["wood"], sit=False)
    # map table: two cartography tables in the middle
    if F.V >= 4:
        for k, u in enumerate((mid - 1, mid)):
            x, z = F.xz(u, F.V // 2 + 1 if F.V > 4 else 3)
            if free(d, R, x, z):
                if pack != "Hearthwood":
                    d.item(x, R.y, z, "cartography_table")
                else:
                    d.item(x, R.y, z, "cartography_table")
    if pack == "Hearthwood":
        for side in (F.left, F.right):
            x, z = wallcells(R, side)[len(wallcells(R, side)) // 2]
            if free(d, R, x, z):
                d.set(x, R.y + 1, z, f"blue_wall_banner[facing={INTO[side]}]")


def f_wash(d, R, M, L, pack):
    sides = door_sides(R)
    long_sides = ["north", "south"] if R.W >= R.D else ["west", "east"]
    side = next((s for s in long_sides if s not in sides), long_sides[0])
    cells = [c for c in wallcells(R, side) if free(d, R, *c)]
    n = 0
    for i, (x, z) in enumerate(cells):
        kind = ["basin", "counter", "brew", "basin", "brew", "counter", "basin"][i % 7]
        if n < 2 and kind == "basin":
            d.item(x, R.y, z, "water_cauldron[level=3]")
            n += 1
        elif kind == "brew":
            d.set(x, R.y, z, slab(M["slab"]))
            d.item(x, R.y + 1, z, "brewing_stand")
        else:
            d.set(x, R.y, z, M["counter"] if pack != "Neoterra" else "smooth_quartz")
            if pack == "Hearthwood":
                d.set(x, R.y + 1, z, "potted_azure_bluet" if i % 2 else "candle[candles=1,lit=false,waterlogged=false]")
    while n < 2:                       # rooms too narrow for the pattern
        for (x, z) in cells:
            if d.air(x, R.y, z):
                d.item(x, R.y, z, "water_cauldron[level=3]")
                n += 1
                break
        else:
            raise RuntimeError("wash room too small")
    # brewing stand count: make sure there are two
    have = d.placed["items"].get("minecraft:brewing_stand", 0)
    for (x, z) in cells:
        if have >= 2:
            break
        if d.air(x, R.y, z):
            d.set(x, R.y, z, slab(M["slab"]))
            d.item(x, R.y + 1, z, "brewing_stand")
            have += 1
    # opposite wall: shower stalls / mangle & towels
    other = OPP[side]
    for i, (x, z) in enumerate(wallcells(R, other)):
        if not free(d, R, x, z) or (R.W <= 3 or R.D <= 3) and False:
            continue
        if pack == "Neoterra" and i % 2 == 0:
            d.set(x, R.y + 2, z, "iron_trapdoor[facing=%s,half=top,open=false,powered=false,waterlogged=false]"
                  % INTO[other])
            d.set(x, R.y - 1, z, "light_blue_concrete")
        elif pack != "Neoterra" and i % 3 == 1 and min(R.W, R.D) > 3:
            d.set(x, R.y, z, "white_carpet")


def f_vault(d, R, M, L, count, along, cross, ender=False, pack=""):
    if along == "x":
        A0, A1, B0, B1 = R.x1, R.x2, R.z1, R.z2

        def xz(a, b):
            return a, b
    else:
        A0, A1, B0, B1 = R.z1, R.z2, R.x1, R.x2

        def xz(a, b):
            return b, a
    D = B1 - B0 + 1
    t = ["B"]
    while len(t) < D:
        t.append("A")
        rem = D - len(t)
        if rem >= 4:
            t += ["B", "B"]
        elif rem == 3:
            t += ["B", "B", "A"]
        elif rem == 2:
            t += ["B", "A"]
        elif rem == 1:
            t += ["B"]
    bcols = [B0 + i for i, c in enumerate(t) if c == "B"]
    # aisle side for barrel facings
    def aisle_dir(b):
        i = b - B0
        if i + 1 < D and t[i + 1] == "A":
            return +1
        return -1
    # order: from the far end towards the cross aisle
    avec = [a for a in range(A0, A1 + 1) if a not in cross]
    c0 = sum(cross) / len(cross)
    avec.sort(key=lambda a: -abs(a - c0))
    n = 0
    for a in avec:
        for b in bcols:
            x, z = xz(a, b)
            if (x, z) in R.keep:
                continue
            for h in range(3):
                if n >= count:
                    break
                sd = aisle_dir(b)
                if h == 2:
                    fac = "up"
                elif along == "x":
                    fac = "south" if sd > 0 else "north"
                else:
                    fac = "east" if sd > 0 else "west"
                d.item(x, R.y + h, z, "barrel", fac)
                n += 1
    if n < count:
        raise RuntimeError(f"vault holds only {n}/{count}")
    # aisle floor markings / lights over the aisles
    acols = [B0 + i for i, c in enumerate(t) if c == "A"]
    for b in acols:
        for a in range(A0, A1 + 1, 4):
            x, z = xz(a + 1 if a + 1 <= A1 else a, b)
            if M["light"] == "flush":
                if flush_ok(d, x, R.top + 1, z):
                    d.set(x, R.top + 1, z, M["lightblock"])
                elif d.air(x, R.top, z):
                    d.set(x, R.top, z, "end_rod[facing=down]")
            elif d.air(x, R.top, z):
                d.lamp(x, R.top, z, "lantern")
    for c in cross:
        for b in range(B0, B1 + 1):
            x, z = xz(c, b)
            if pack == "Neoterra" and d.air(x, R.y, z) and (x, z) not in R.keep:
                d.set(x, R.y - 1, z, "yellow_concrete" if b % 2 else "black_concrete")
    if ender:
        for c in cross:
            for b in (B1, B0):
                x, z = xz(c, b)
                if free(d, R, x, z):
                    d.item(x, R.y, z, "ender_chest", "north" if along == "x" else "west")
                    return n
        raise RuntimeError("no room for the ender chest")
    return n


def f_archive(d, R, M, L, n_shelf, n_chis, pack):
    sides = door_sides(R)
    order = [s for s in ("north", "west", "east", "south") if s not in sides] + [s for s in sides]
    cells = []
    for s in order:
        for (x, z) in wallcells(R, s):
            if (x, z) in R.keep or any((x, z) == c[:2] for c in cells):
                continue
            # keep the cells next to a door free so the door is not walled in
            if any(abs(x - kx) + abs(z - kz) == 1 and (x in (R.x1, R.x2) and z in (R.z1, R.z2)) for kx, kz in R.keep):
                continue
            cells.append((x, z, INTO[s]))
    need = n_shelf + n_chis
    i = 0
    k = 0
    for (x, z, fac) in cells:
        for h in range(3):
            if k < n_shelf:
                d.bookshelf(x, R.y + h, z)
            elif k < need:
                d.item(x, R.y + h, z, chiseled(fac, k))
            k += 1
        if k >= need:
            i += 1
            break
    if k < need:
        raise RuntimeError(f"archive holds only {k}/{need}")
    # bare stretches of wall: display banners
    used = set((x, z) for x, z, _ in cells[:(need + 2) // 3])
    for (x, z, fac) in cells[(need + 2) // 3:]:
        if d.air(x, R.y, z) and (x + z) % 3 == 0:
            d.set(x, R.y + 1, z, f"{'cyan' if pack == 'Neoterra' else 'red' if pack == 'Hearthwood' else 'green'}"
                                 f"_wall_banner[facing={fac}]")
    # centre: enchanting table on a rug between two lecterns, reading table with chairs
    cx, cz = (R.x1 + R.x2) // 2, (R.z1 + R.z2) // 2
    along_x = R.W >= R.D
    if along_x:
        d.rug(cx - 2, cz - 1, cx + 2, cz + 1, R.y, (M["rug"], M["rug2"]), "border")
        d.set(cx, R.y, cz, AIR)
        d.item(cx, R.y, cz, "enchanting_table")
        d.set(cx - 2, R.y, cz, AIR)
        d.set(cx + 2, R.y, cz, AIR)
        d.item(cx - 2, R.y, cz, "lectern", "east")
        d.item(cx + 2, R.y, cz, "lectern", "west")
        tz = cz + 3 if cz + 3 <= R.z2 - 2 else cz - 3
        if R.z1 + 2 <= tz <= R.z2 - 2:
            for x in range(cx - 1, cx + 2):
                d.table(x, R.y, tz, M["wood"], "slab", M["slab"])
                d.chair(x, R.y, tz - 1, "north", M["wood"], sit=False)
                d.chair(x, R.y, tz + 1, "south", M["wood"], sit=False)
    else:
        d.rug(cx - 1, cz - 2, cx + 1, cz + 2, R.y, (M["rug"], M["rug2"]), "border")
        d.set(cx, R.y, cz, AIR)
        d.item(cx, R.y, cz, "enchanting_table")
        d.set(cx, R.y, cz - 2, AIR)
        d.set(cx, R.y, cz + 2, AIR)
        d.item(cx, R.y, cz - 2, "lectern", "south")
        d.item(cx, R.y, cz + 2, "lectern", "north")


def f_workshop(d, R, M, L, pack, outdoor=False, order=None):
    items = [("anvil", "a"), ("grindstone", "a"), ("smithing_table", None), ("crafting_table", None),
             ("stonecutter", None), ("fletching_table", None), ("loom", None), ("crafting_table", None),
             ("smithing_table", None), ("grindstone", "a"), ("anvil", "a"), ("crafting_table", None)]
    sides = door_sides(R)
    order = order or [s for s in ("north", "east", "west", "south") if s not in sides]
    cells = []
    for s in order:
        for (x, z) in wallcells(R, s):
            if free(d, R, x, z) and (x, z) not in [c[:2] for c in cells]:
                cells.append((x, z, INTO[s]))
    k = 0
    for i, (x, z, fac) in enumerate(cells):
        if k >= len(items):
            # spare wall: tool rack (trapdoors) above a chest / barrel of stock
            if i % 2 == 0:
                d.set(x, R.y, z, f"chest[facing={fac},type=single,waterlogged=false]")
            continue
        name, kind = items[k]
        if kind == "a":
            fac2 = CW[fac]
            d.item(x, R.y, z, name, fac2)
        else:
            d.item(x, R.y, z, name, fac)
        if not outdoor and d.air(x, R.y + 2, z):
            d.set(x, R.y + 2, z, "lantern[hanging=false,waterlogged=false]" if k % 4 == 1 else AIR)
        k += 1
    if k < len(items):
        raise RuntimeError(f"workshop fits only {k}/{len(items)} work blocks")


def f_generator(d, R, M, L, pack):
    sides = door_sides(R)
    long_sides = ["north", "south"] if R.W >= R.D else ["west", "east"]
    side = next((s for s in long_sides if s not in sides), long_sides[0])
    fac = INTO[side]
    units = ["furnace"] * 4 + ["blast_furnace"] * (0 if L < 2 else 1 if L < 3 else 2)
    cells = [c for c in wallcells(R, side) if free(d, R, *c)]
    off = max(0, (len(cells) - len(units)) // 2)
    hood = {"Neoterra": "iron_block", "Hearthwood": "bricks", "Cascadia": "cobblestone"}[pack]
    for i, (x, z) in enumerate(cells):
        j = i - off
        if 0 <= j < len(units):
            d.item(x, R.y, z, units[j], fac)
            d.set(x, R.y + 1, z, hood)
            d.set(x, R.y + 2, z, "chain[axis=y,waterlogged=false]" if pack != "Hearthwood" else hood)
        elif pack == "Neoterra":
            d.set(x, R.y, z, "iron_block")
            d.set(x, R.y + 1, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # boiler / turbine in the middle of the room
    cx, cz = (R.x1 + R.x2) // 2, (R.z1 + R.z2) // 2
    dx, dz = D4[fac]
    bx, bz = cx, cz + dz if R.D > 5 else cz
    if R.W >= R.D:
        cells2 = [(bx - 1, bz), (bx, bz), (bx + 1, bz)]
    else:
        cells2 = [(bx, bz - 1), (bx, bz), (bx, bz + 1)]
    if pack == "Neoterra":
        for i, (x, z) in enumerate(cells2):
            d.set(x, R.y, z, "cut_copper" if i != 1 else "copper_block")
            d.set(x, R.y + 1, z, "waxed_copper_grate" if i == 1 else "cut_copper_slab[type=bottom,waterlogged=false]")
        x, z = cells2[1]
        d.set(x, R.y + 2, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    elif pack == "Hearthwood":
        for i, (x, z) in enumerate(cells2):
            d.set(x, R.y, z, "bricks" if i != 1 else "water_cauldron[level=3]")
            if i == 1:
                d.set(x, R.y + 1, z, "copper_block")
                d.set(x, R.y + 2, z, "chain[axis=y,waterlogged=false]")
    else:
        for i, (x, z) in enumerate(cells2):
            d.set(x, R.y, z, "iron_block")
            d.set(x, R.y + 1, z, "iron_block" if i == 1 else "iron_bars")
        x, z = cells2[1]
        d.set(x, R.y + 2, z, "chain[axis=y,waterlogged=false]")
    # control panel on the opposite wall
    other = OPP[side]
    for i, (x, z) in enumerate(wallcells(R, other)):
        if not free(d, R, x, z) or i == 0 or i == len(wallcells(R, other)) - 1:
            continue
        if i % 2:
            d.set(x, R.y + 1, z, f"lever[face=wall,facing={INTO[other]},powered=false]")
        if pack == "Neoterra" and i % 3 == 0:
            d.set(x, R.y + 2, z, f"stone_button[face=wall,facing={INTO[other]},powered=false]")


def f_pantry(d, R, M, L, pack):
    sides = door_sides(R)
    cells = []
    for s in [s for s in ("north", "south", "east", "west") if s not in sides]:
        for (x, z) in wallcells(R, s):
            if free(d, R, x, z) and (x, z) not in [c[:2] for c in cells]:
                cells.append((x, z, INTO[s]))
    want = ["composter"] * 3 + ["smoker"] * (0 if L < 4 else 1 if L < 5 else 2)
    k = 0
    for i, (x, z, fac) in enumerate(cells):
        if k < len(want):
            d.item(x, R.y, z, want[k], fac)
            k += 1
        else:
            m = i % 4
            if m == 0:
                d.set(x, R.y, z, "hay_block[axis=y]")
                d.set(x, R.y + 1, z, "hay_block[axis=x]")
            elif m == 1:
                d.set(x, R.y, z, "melon" if pack != "Hearthwood" else "pumpkin")
            elif m == 2:
                d.set(x, R.y, z, f"barrel[facing={fac},open=false]")
                d.set(x, R.y + 1, z, "barrel[facing=up,open=false]")
            else:
                d.set(x, R.y, z, "pumpkin" if pack != "Neoterra" else "dried_kelp_block")
    if k < len(want):
        raise RuntimeError("pantry too small")


# ---------------------------------------------------------------------------------------------------- children
def c_kitchen(d, R, M, L, pack):
    sides = door_sides(R)
    far = next(s for s in ("north", "east", "west", "south") if s not in sides and OPP[s] in sides) \
        if any(OPP[s] in sides for s in ("north", "east", "west", "south") if s not in sides) else \
        next(s for s in ("north", "east", "west", "south") if s not in sides)
    F = Frame(R, far)
    stations = ["crafting", "sink"] + ["furnace"] * L + ["smoker", "rack"]
    k = 0
    u = 0
    line = []
    while k < len(stations) and u < F.U:
        x, z = F.xz(u, 0)
        if free(d, R, x, z):
            line.append((x, z, stations[k]))
            k += 1
        u += 1
    # overflow onto the side walls
    v = 1
    while k < len(stations) and v < F.V - 2:
        for uu in (0, F.U - 1):
            if k >= len(stations):
                break
            x, z = F.xz(uu, v)
            if free(d, R, x, z):
                line.append((x, z, stations[k]))
                k += 1
        v += 1
    if k < len(stations):
        raise RuntimeError("kitchen too small")
    fac = F.back
    for x, z, s in line:
        uv = F.uv(x, z)
        face = fac if uv[1] == 0 else (F.right if uv[0] == 0 else F.left)
        if s == "furnace":
            d.item(x, R.y, z, "furnace", face)
            dx, dz = D4[face]
            d.spot(x + dx, R.y, z + dz, "work")
        elif s == "smoker":
            d.item(x, R.y, z, "smoker", face)
        elif s == "crafting":
            d.item(x, R.y, z, "crafting_table")
        elif s == "rack":
            d.rack(x, R.y, z, face)
        else:
            d.set(x, R.y, z, "water_cauldron[level=3]")
        if s in ("furnace", "smoker"):
            d.set(x, R.y + 2, z, {"Neoterra": "iron_trapdoor[facing=%s,half=top,open=false,powered=false,"
                                               "waterlogged=false]" % face,
                                  "Hearthwood": "bricks", "Cascadia": "cobblestone"}[pack])
    # rest of the front wall: counter with jars
    for uu in range(F.U):
        x, z = F.xz(uu, 0)
        if free(d, R, x, z):
            d.set(x, R.y, z, slab(M["slab"]) if pack != "Neoterra" else "smooth_quartz")
            d.set(x, R.y + 1, z, "decorated_pot[cracked=false,facing=%s,waterlogged=false]" % fac if uu % 2
                  else "candle[candles=1,lit=false,waterlogged=false]")
    # mess tables
    need = 4 if L < 3 else 6
    mark_keep(d, R)
    got = 0
    for vv in range(3, F.V - 1, 3):
        for uu in range(1, F.U - 1, 3):
            if got >= need:
                break
            cells = [F.xz(uu + a, vv + b) for a in (-1, 0, 1) for b in (-1, 0, 1)]
            if not all(R.x1 <= cx <= R.x2 and R.z1 <= cz <= R.z2 and free(d, R, cx, cz) for cx, cz in cells):
                continue
            cx, cz = F.xz(uu, vv)
            d.table(cx, R.y, cz, M["wood"], "post")
            for s in (F.left, F.right, F.front, F.back):
                if got >= need:
                    break
                dx, dz = D4[s]
                d.chair(cx + dx, R.y, cz + dz, s, M["wood"])
                got += 1
    # long bench table if the grid did not fit
    if got < need:
        for vv in range(2, F.V):
            for uu in range(F.U):
                if got >= need:
                    break
                x, z = F.xz(uu, vv)
                if free(d, R, x, z) and uu in (0, F.U - 1):
                    d.chair(x, R.y, z, F.left if uu == 0 else F.right, M["wood"])
                    got += 1
    mark_keep(d, R, False)
    if got < need:
        raise RuntimeError("kitchen seats")


def c_clinic(d, R, M, L, pack):
    n = 2 * L
    sides = door_sides(R)
    long_sides = ["north", "south"] if R.W >= R.D else ["west", "east"]
    placed = 0
    walls = {s: [c for c in wallcells(R, s)] for s in long_sides}
    idx = {s: 0 for s in long_sides}
    last = {s: -9 for s in long_sides}
    turn = 0
    while placed < n:
        s = long_sides[turn % 2]
        turn += 1
        cells = walls[s]
        while idx[s] < len(cells):
            i = idx[s]
            idx[s] += 1
            x, z = cells[i]
            dx, dz = D4[INTO[s]]
            if i - last[s] < 2 or not (free(d, R, x, z) and free(d, R, x + dx, z + dz)):
                continue
            d.bed(x, R.y, z, s, "white")
            last[s] = i
            placed += 1
            # bedside cabinet / screen
            sx, sz = D4[CW[s]] if s in ("north", "west") else D4[OPP[CW[s]]]
            nx, nz = x + sx, z + sz
            if R.x1 <= nx <= R.x2 and R.z1 <= nz <= R.z2 and free(d, R, nx, nz):
                d.set(nx, R.y, nz, slab(M["slab"]))
                d.set(nx, R.y + 1, nz, "white_stained_glass_pane" if pack == "Neoterra" else
                      "potted_white_tulip" if pack == "Hearthwood" else "potted_lily_of_the_valley")
            break
        if all(idx[t] >= len(walls[t]) for t in long_sides) and placed < n:
            raise RuntimeError(f"clinic fits {placed}/{n} beds")
    # nurse station on a short wall
    short = [s for s in ("west", "east", "north", "south") if s not in long_sides and s not in sides] or \
        [s for s in ("west", "east", "north", "south") if s not in long_sides]
    cells = [c for c in wallcells(R, short[0]) if free(d, R, *c)]
    want = ["barrel", "furnace"] + (["brewing_stand"] if L >= 3 else []) + ["sink"]
    for (x, z), w in zip(cells[len(cells) // 2 - 1:] if len(cells) >= 4 else cells, want):
        if w == "barrel":
            d.item(x, R.y, z, "barrel", "up")
        elif w == "furnace":
            d.item(x, R.y, z, "furnace", INTO[short[0]])
        elif w == "brewing_stand":
            d.item(x, R.y, z, "brewing_stand")
        else:
            d.set(x, R.y, z, "water_cauldron[level=3]")
    if d.placed["items"].get("minecraft:barrel", 0) < 1 or d.placed["items"].get("minecraft:furnace", 0) < 1:
        raise RuntimeError("clinic station")
    # floor runner down the ward
    if long_sides[0] == "north":
        zc = (R.z1 + R.z2) // 2
        for x in range(R.x1 + 1, R.x2):
            if free(d, R, x, zc):
                d.set(x, R.y, zc, "light_blue_carpet" if pack == "Neoterra" else "white_carpet")


def c_school(d, R, M, L, pack):
    sides = door_sides(R)
    shorts = ["west", "east"] if R.W >= R.D else ["north", "south"]
    front = next((s for s in shorts if s not in sides), next(s for s in ("west", "east", "north", "south")
                                                             if s not in sides))
    F = Frame(R, front)
    keep_uv = [F.uv(x, z) for x, z in R.keep]
    shift = 1 if any(k and k[0] == 0 and k[1] >= 2 for k in keep_uv) else 0
    cut = 1 if any(k and k[0] == F.U - 1 and k[1] >= 2 for k in keep_uv) else 0
    cols = [u for u in range(shift, F.U - cut) if (u - shift) % 3 != 2]
    mid = F.U // 2
    # blackboard above the teacher's spot
    for u in range(max(0, mid - 1), min(F.U, mid + 2)):
        x, z = F.xz(u, 0)
        if (x, z) not in R.keep:
            d.set(x, R.y + 1, z, "black_concrete" if pack == "Neoterra" else "black_terracotta" if pack == "Hearthwood"
                  else "dark_oak_planks")
            d.set(x, R.y + 2, z, "black_concrete" if pack == "Neoterra" else "black_terracotta" if pack == "Hearthwood"
                  else "dark_oak_planks")
            d.set(x, R.y, z, slab(M["slab"]))
    x, z = F.xz(mid, 1)
    d.spot(x, R.y, z, "work")
    # teacher's desk to one side
    tu = mid + 2 if mid + 2 < F.U else mid - 2
    x, z = F.xz(tu, 1)
    if free(d, R, x, z):
        d.set(x, R.y, z, f"{M['wood']}_planks" if pack != "Neoterra" else "smooth_quartz")
        d.set(x, R.y + 1, z, "lantern[hanging=false,waterlogged=false]" if pack != "Neoterra"
              else "potted_bamboo")
    # pupils' desks: desk (trapdoor top / slab) in front, chair behind it facing the board
    seats = 0
    v = 3
    while seats < 10 and v + 1 < F.V - 1:
        for u in cols:
            if seats >= 10:
                break
            dx_, dz_ = F.xz(u, v)
            cx, cz = F.xz(u, v + 1)
            if free(d, R, dx_, dz_) and free(d, R, cx, cz):
                d.set(dx_, R.y, dz_, slab(M["slab"]) if pack != "Hearthwood" else trap("oak", F.front))
                d.chair(cx, R.y, cz, F.back, M["wood"])
                seats += 1
        v += 2
    if seats < 10:
        raise RuntimeError(f"school seats {seats}")
    # bookshelves along the back wall, two high
    n = {1: 2, 2: 4, 3: 6, 4: 8, 5: 10}[L]
    k = 0
    for u in range(F.U):
        if k >= n:
            break
        x, z = F.xz(u, F.V - 1)
        if free(d, R, x, z, 2):
            d.bookshelf(x, R.y, z, 2)
            k += 2
    for u in (0, F.U - 1):                       # spill into the front corners
        if k >= n:
            break
        x, z = F.xz(u, 0)
        if free(d, R, x, z, 2):
            d.bookshelf(x, R.y, z, 2)
            k += 2
    if k < n:
        raise RuntimeError("school shelves")
    if pack != "Neoterra":
        for u in (0, F.U - 1):
            x, z = F.xz(u, 2)
            if free(d, R, x, z) and d.air(x, R.y + 1, z):
                d.set(x, R.y + 1, z, "%s_wall_banner[facing=%s]" % ("blue" if pack == "Hearthwood" else "green",
                                                                    F.right if u == 0 else F.left))


def c_farm(d, R, M, L, pack):
    sides = door_sides(R)
    # the front (service) wall is the wall of the main door (first door side found in a fixed order)
    front = next(s for s in ("north", "west", "east", "south") if s in sides)
    F = Frame(R, front)
    keep_uv = [F.uv(x, z) for x, z in R.keep]
    paths = {0, F.U - 1} | {k[0] for k in keep_uv if k and k[1] >= 2}
    # service row v = 0: racks, barrel, composter, a stool
    want = ["rack"] * L + ["barrel", "composter", "chair"]
    k = 0
    for u in range(F.U):
        x, z = F.xz(u, 0)
        if k >= len(want) or not free(d, R, x, z):
            continue
        w = want[k]
        if w == "rack":
            d.rack(x, R.y, z, F.back)
        elif w == "barrel":
            d.item(x, R.y, z, "barrel", "up")
        elif w == "composter":
            d.item(x, R.y, z, "composter")
        else:
            d.chair(x, R.y, z, F.front, M["wood"])
        k += 1
    if k < len(want):
        raise RuntimeError("farm service row too short")
    # grow beds from v = 2: rows of crops either side of irrigation channels, paths at the ends
    crops = ["wheat[age=7]", "carrots[age=7]", "potatoes[age=7]", "beetroots[age=3]"]
    pathblock = {"Neoterra": "polished_andesite", "Hearthwood": "gravel", "Cascadia": "coarse_dirt"}[pack]
    pat = []
    run = 0
    for u in range(F.U):
        if u in paths:
            pat.append("P")
            run = 0
        else:
            run += 1
            pat.append("W" if run % 3 == 2 and u + 1 < F.U and (u + 1) not in paths or run % 3 == 2 and False
                       else "C")
    # make sure every crop is within 4 of water
    for u in range(F.U):
        if pat[u] == "C" and not any(pat[w] == "W" for w in range(max(0, u - 4), min(F.U, u + 5))):
            pat[u] = "W"
    for u in range(F.U):
        for v in range(2, F.V):
            x, z = F.xz(u, v)
            if (x, z) in R.keep:
                continue
            c = pat[u]
            if c == "P":
                d.set(x, R.y - 1, z, pathblock)
            elif c == "W":
                d.set(x, R.y - 1, z, "water[level=0]")
                if v % 2 == 0 or pack == "Neoterra":
                    d.set(x, R.top, z, {"Neoterra": "sea_lantern", "Hearthwood": "glowstone",
                                        "Cascadia": "ochre_froglight[axis=y]"}[pack])
            else:
                d.set(x, R.y - 1, z, "farmland[moisture=7]")
                d.set(x, R.y, z, crops[(u + v // 3) % len(crops)])
    for u in range(F.U):                   # walkway in front of the service row
        x, z = F.xz(u, 1)
        if d.air(x, R.y, z):
            d.set(x, R.y - 1, z, pathblock)
    # path lights over the service walkway
    for u in range(1, F.U, 4):
        x, z = F.xz(u, 1)
        if M["light"] == "flush":
            d.set(x, R.top, z, "end_rod[facing=down]")
        else:
            d.lamp(x, R.top, z, "lantern")


CHILD_FN = {"kitchen": c_kitchen, "clinic": c_clinic, "school": c_school, "farm": c_farm}


CORR_KINDS = ("corr", "hall")


def active(pack, L):
    return [s for s in PLANS[pack]["spaces"] if s[6] <= L]


def level_doors(pack, L):
    """Doors at level L: one per room onto the first adjacent corridor (plan order) + the plan's extra doors."""
    sp = active(pack, L)
    cors = [s for s in sp if s[0] in CORR_KINDS]
    out = []
    for (k, dk, x1, z1, x2, z2, ml) in sp:
        if k in CORR_KINDS:
            continue
        for (ck, cd, cx1, cz1, cx2, cz2, _) in cors:
            if cd != dk:
                continue
            door = None
            ox1, ox2 = max(x1, cx1), min(x2, cx2)
            oz1, oz2 = max(z1, cz1), min(z2, cz2)
            if ox1 <= ox2:
                if z2 + 2 == cz1:
                    door = ((ox1 + ox2) // 2, z2 + 1)
                elif cz2 + 2 == z1:
                    door = ((ox1 + ox2) // 2, z1 - 1)
            if door is None and oz1 <= oz2:
                if x2 + 2 == cx1:
                    door = (x2 + 1, (oz1 + oz2) // 2)
                elif cx2 + 2 == x1:
                    door = (x1 - 1, (oz1 + oz2) // 2)
            if door:
                out.append((door[0], door[1], dk, "vault" if k == "vault" else "door"))
                break
    for (x, z, dk, ml, kind) in PLANS[pack]["doors"]:
        if ml <= L:
            out.append((x, z, dk, kind))
    return out


def keep_for(pack, L, deck, x1, z1, x2, z2):
    keep = set()
    for (x, z, dk, k) in level_doors(pack, L):
        if dk != deck:
            continue
        for dx, dz in D4.values():
            if x1 <= x + dx <= x2 and z1 <= z + dz <= z2:
                keep.add((x + dx, z + dz))
    return keep


def child_geom(pack, kind, L):
    P = PLANS[pack]
    sp = next(s for s in P["spaces"] if s[0] == kind)
    _, deck, x1, z1, x2, z2, minL = sp
    fy, top = LV[deck]
    return deck, (x1, z1, x2, z2), fy, top, keep_for(pack, L, deck, x1, z1, x2, z2), P["child_huts"][kind]


def child_box_top(deck):
    """Deck-A rooms own their ceiling; deck-B rooms stop under the shared slab (deck A's floor / another child)."""
    return LV[deck][1] + 1 if deck == "A" else LV[deck][1]


def child_design(kind, pack, rel, L):
    deck, (x1, z1, x2, z2), fy, top, keep, (hx, hz) = child_geom(pack, kind, L)
    M = MATS[pack]
    W, D = x2 - x1 + 1, z2 - z1 + 1
    Hh = child_box_top(deck) - fy + 1
    d = Design(pack, rel, (W, Hh, D), gy=0, paving=M["child_floor"][kind])
    cy = Hh - 1 if deck == "A" else Hh
    for x in range(W if deck == "A" else 0):
        for z in range(D):
            if pack == "Hearthwood":
                c = "dark_oak_planks" if (x % 3 == 1) else "stone_bricks"
            elif pack == "Cascadia":
                c = "stripped_spruce_log[axis=x]" if z % 3 == 1 else "spruce_planks"
            else:
                c = "white_concrete"
            d.set(x, cy, z, c)
    lk = {(x - x1, z - z1) for x, z in keep}
    R = room(0, 0, W - 1, D - 1, 1, cy - 1, lk | {(hx - x1, hz - z1)})
    d.hut(hx - x1, 1, hz - z1, "north")
    CHILD_FN[kind](d, R, M, L, pack)
    if kind != "farm":
        lights(d, R, M, cy, 4, skip=())
        dress(d, R, M, pack, kind)
    return d


@design("bunkerkitchen")
def bunkerkitchen(pack, rel, L):
    return child_design("kitchen", pack, rel, L)


@design("bunkerclinic")
def bunkerclinic(pack, rel, L):
    return child_design("clinic", pack, rel, L)


@design("bunkerschool")
def bunkerschool(pack, rel, L):
    return child_design("school", pack, rel, L)


@design("bunkerfarm")
def bunkerfarm(pack, rel, L):
    return child_design("farm", pack, rel, L)


def is_earth(d, x, y, z):
    return d.get(x, y, z) == "structurize:" + SOLID.split(":")[1]


def put_wall(d, pack, x, y, z, fy):
    if d.bp.inside(x, y, z) and is_earth(d, x, y, z):
        d.set(x, y, z, wall_block(pack, x, y, z, fy))


def carve_underground(d, pack, L):
    P = PLANS[pack]
    M = MATS[pack]
    spaces = [s for s in P["spaces"] if s[6] <= L]
    # shells
    for kind, deck, x1, z1, x2, z2, _ in spaces:
        fy, top = LV[deck]
        for y in range(fy, top + 2):
            for z in range(z1 - 1, z2 + 2):
                for x in range(x1 - 1, x2 + 2):
                    put_wall(d, pack, x, y, z, fy)
    # interiors: deck B first, deck A's floor wins on the shared slab
    for deck in ("B", "A"):
        fy, top = LV[deck]
        for kind, dk, x1, z1, x2, z2, _ in spaces:
            if dk != deck:
                continue
            fl = M["floor"].get(kind, M["floor"]["default"])
            for z in range(z1, z2 + 1):
                for x in range(x1, x2 + 1):
                    d.set(x, fy, z, fl)
                    for y in range(fy + 1, top + 1):
                        d.set(x, y, z, AIR)
                    d.set(x, top + 1, z, M["ceil"])
    return spaces


def ribs(d, pack, sp):
    """Structural ribs: Neoterra concrete pilasters + cyan band, Hearthwood springers and beams, Cascadia timber sets."""
    kind, deck, x1, z1, x2, z2, _ = sp
    fy, top = LV[deck]
    along_x = (x2 - x1) >= (z2 - z1)
    if along_x:
        rng = range(x1, x2 + 1)
        walls = [(z1 - 1, "south"), (z2 + 1, "north")]
    else:
        rng = range(z1, z2 + 1)
        walls = [(x1 - 1, "east"), (x2 + 1, "west")]
    step = 4 if pack != "Cascadia" else 3
    for i, a in enumerate(rng):
        on = (i % step == 1)
        for (b, fac) in walls:
            x, z = (a, b) if along_x else (b, a)
            if not d.bp.inside(x, fy, z):
                continue
            wall_here = all(not d.air(x, y, z) and "door" not in d.get(x, y, z) for y in range(fy + 1, top + 1))
            ix, iz = (a, b + (1 if fac == "south" else -1)) if along_x else (b + (1 if fac == "east" else -1), a)
            if pack == "Neoterra":
                if wall_here and kind in ("corr", "hall"):
                    d.set(x, fy + 2, z, "cyan_terracotta")
                if on and wall_here:
                    for y in range(fy + 1, top + 1):
                        d.set(x, y, z, "gray_concrete")
            elif pack == "Hearthwood":
                if wall_here and d.air(ix, top, iz):
                    d.set(ix, top, iz, st("stone_brick_stairs", OPP[INTO[fac]] if False else fac_to_wall(fac),
                                          "top"))
                if on and wall_here:
                    for y in range(fy + 1, top + 1):
                        d.set(x, y, z, "chiseled_stone_bricks" if y == top else "stone_bricks")
            else:
                if on and wall_here:
                    for y in range(fy + 1, top + 1):
                        d.set(x, y, z, "spruce_log[axis=y]")
        if on:
            for b in (range(z1, z2 + 1) if along_x else range(x1, x2 + 1)):
                x, z = (a, b) if along_x else (b, a)
                if "substitution" in d.get(x, top + 1, z):
                    continue
                if pack == "Hearthwood":
                    d.set(x, top + 1, z, "dark_oak_log[axis=%s]" % ("z" if along_x else "x"))
                elif pack == "Cascadia":
                    d.set(x, top + 1, z, "spruce_log[axis=%s]" % ("z" if along_x else "x"))


def fac_to_wall(fac):
    """`fac` = direction from the wall into the room; a springer's tall back faces the wall."""
    return OPP[fac]


def make_ramp(d, pack, L):
    """Straight stair from the surface (walk SW) down to deck A (walk 19), descending south."""
    P = PLANS[pack]
    M = MATS[pack]
    x0, w, zf = P["ramp"]
    fyA = LV["A"][0]
    for i in range(1, 7):
        z = zf + i - 1
        stand = SW - i
        blk = stand - 1
        for x in range(x0, x0 + w):
            for y in range(fyA, blk):
                d.set(x, y, z, M["solid"])
            d.set(x, blk, z, st(M["step"], "north"))
            for y in range(stand, stand + 4):
                d.set(x, y, z, AIR)
            put_wall(d, pack, x, stand + 4, z, fyA)
            if stand + 4 <= GY:
                if d.get(x, stand + 4, z) not in (AIR,) and not d.air(x, stand + 4, z):
                    pass
        for x in (x0 - 1, x0 + w):
            for y in range(fyA, stand + 5):
                put_wall(d, pack, x, y, z, fyA)
    # lights on the side walls of the ramp
    for i in (2, 5):
        z = zf + i - 1
        stand = SW - i
        if pack == "Neoterra":
            d.set(x0 - 1, stand + 2, z, "sea_lantern")
            d.set(x0 + w, stand + 2, z, "sea_lantern")
        else:
            if not d.air(x0 - 1, stand + 2, z):
                d.set(x0, stand + 2, z, "wall_torch[facing=east]") if False else None


def reclear_ramp(d, pack):
    """After the surface work: the ramp's head (cells at or above ground level) must stay open."""
    x0, w, zf = PLANS[pack]["ramp"]
    for i in range(1, 7):
        z = zf + i - 1
        stand = SW - i
        for x in range(x0, x0 + w):
            for y in range(max(stand, GY), stand + 4):
                d.set(x, y, z, AIR)


@@TAIL@@
