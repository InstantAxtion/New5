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
LV = {"A": (18, 21), "B": (13, 17), "C": (8, 12)}          # deck -> (floor y, top air y); ceiling = top + 1
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
    wells=[(30, 28, "A", "B", 2, +1), (30, 46, "B", "C", 5, +1)],          # lane-1 x, z0, upper deck, lower deck, minL, lane-2 side
    spaces=[
        # ---- deck A
        ("hall", "A", 22, 11, 32, 14, 1),
        ("corr", "A", 26, 15, 28, 33, 1),
        ("corr", "A", 2, 24, 25, 26, 1),
        ("corr", "A", 29, 24, 40, 26, 1),
        ("corr", "A", 41, 24, 52, 26, 2),
        ("corr", "A", 26, 34, 28, 52, 3),
        ("corr", "A", 2, 42, 52, 44, 3),
        ("vault", "A", 13, 1, 23, 9, 1),
        ("archive", "A", 31, 1, 44, 9, 1),
        ("radio", "A", 46, 1, 52, 9, 4),
        ("clinic", "A", 2, 16, 12, 22, 1),
        ("kitchen", "A", 14, 16, 24, 22, 1),
        ("dorm", "A", 30, 16, 40, 22, 1),
        ("mess", "A", 42, 16, 52, 22, 3),
        ("school", "A", 2, 28, 12, 34, 1),
        ("common", "A", 14, 28, 24, 34, 1),
        ("workroom", "A", 33, 28, 40, 34, 1),
        ("ops", "A", 42, 28, 52, 34, 3),
        ("laundry", "A", 2, 36, 12, 40, 3),
        ("lab", "A", 14, 36, 24, 40, 3),
        ("gym", "A", 30, 36, 40, 40, 4),
        ("office", "A", 42, 36, 52, 40, 4),
        ("chapel", "A", 2, 46, 12, 52, 4),
        ("bunks", "A", 14, 46, 24, 52, 5),
        ("store", "A", 30, 46, 40, 52, 4),
        ("canteen", "A", 42, 46, 52, 52, 4),
        # ---- deck B
        ("corr", "B", 2, 24, 52, 26, 2),
        ("corr", "B", 26, 2, 28, 23, 2),
        ("corr", "B", 26, 27, 28, 52, 4),
        ("fabrication", "B", 2, 16, 12, 22, 3),
        ("generator", "B", 14, 16, 24, 22, 3),
        ("farm", "B", 30, 16, 40, 22, 2),
        ("pantry", "B", 42, 16, 52, 22, 2),
        ("water", "B", 2, 2, 12, 14, 4),
        ("vault", "B", 14, 2, 24, 14, 2),
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
        ("fabrication", "B", 2, 46, 12, 52, 5),
        ("records", "B", 14, 46, 24, 52, 5),
        ("mess", "B", 33, 46, 40, 52, 5),
        # ---- deck C (plant deck)
        ("corr", "C", 2, 42, 52, 44, 5),
        ("reactor", "C", 2, 34, 12, 40, 5),
        ("turbine", "C", 14, 34, 24, 40, 5),
        ("power", "C", 26, 34, 36, 40, 5),
        ("water", "C", 38, 34, 52, 40, 5),
        ("cistern", "C", 2, 46, 12, 52, 5),
        ("server", "C", 14, 46, 27, 52, 5),
        ("armory", "C", 34, 46, 44, 52, 5),
        ("store", "C", 46, 46, 52, 52, 5),
        ("power", "B", 42, 46, 52, 52, 5),
    ],
    doors=[(45, 5, "A", 4, "door"), (13, 49, "B", 5, "door"), (41, 49, "B", 5, "door"), (7, 15, "B", 4, "door"), (47, 15, "B", 4, "door"),
           (13, 40, "B", 5, "door"), (41, 40, "B", 5, "door"), (29, 46, "B", 5, "open"), (31, 45, "C", 5, "open"),
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
    "Neoterra": dict(size=(55, 58, 55), **_transform(BASE, 55)),
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


def f_vault(d, R, M, L, count, along, cross, ender=False, pack="", fill_all=False):
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
    if n < count and not fill_all:
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
            if any(abs(x - kx) + abs(z - kz) == 1 for kx, kz in R.keep):
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
    for deck in ("C", "B", "A"):
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


def make_wells(d, pack, L):
    """Compact U-shaped stair cores between decks (5 steps down)."""
    M = MATS[pack]
    for (x0, z0, up, lo, ml, side) in PLANS[pack]["wells"]:
        if ml > L:
            continue
        wu = LV[up][0] + 1
        tu = LV[up][1]
        fl, tl = LV[lo]
        l1, l2 = x0, x0 + side
        xa, xb = min(l1, l2), max(l1, l2)
        for y in range(fl, tu + 2):
            for z in range(z0 - 1, z0 + 5):
                for x in range(xa - 1, xb + 2):
                    put_wall(d, pack, x, y, z, fl if y <= tl + 1 else LV[up][0])
        for x in (l1, l2):
            for z in range(z0, z0 + 4):
                for y in range(fl, tu + 1):
                    d.set(x, y, z, wall_block(pack, x, y, z, fl) if pack != "Neoterra" else "light_gray_concrete")
        to_l1 = "west" if side > 0 else "east"
        cells = [
            (l1, z0, None, None, wu, tu),
            (l1, z0 + 1, wu - 2, "north", wu - 1, wu + 2),
            (l1, z0 + 2, wu - 3, "north", wu - 2, wu + 1),
            (l1, z0 + 3, wu - 4, "north", wu - 3, wu),
            (l2, z0 + 3, wu - 5, to_l1, wu - 4, wu - 1),
            (l2, z0 + 2, wu - 6, "south", wu - 5, wu - 2),
            (l2, z0 + 1, None, None, fl + 1, tl),
            (l2, z0, None, None, fl + 1, tl),
        ]
        for (x, z, sy, fac, c0, c1) in cells:
            if sy is None:
                d.set(x, c0 - 1, z, M["floor"]["corr"])
                for y in range(fl, c0 - 1):
                    d.set(x, y, z, M["solid"])
            else:
                for y in range(fl, sy):
                    d.set(x, y, z, M["solid"])
                d.set(x, sy, z, st(M["step"], fac))
            for y in range(c0, c1 + 1):
                d.set(x, y, z, AIR)
        for z in (z0, z0 + 1):
            d.set(l2, tl + 1, z, M["ceil"])
        if pack == "Neoterra":
            d.set(l1, tu, z0 + 3, "sea_lantern")
            d.set(l2, tl, z0 + 1, "end_rod[facing=down]")
        else:
            d.set(l2, tl, z0 + 1, "lantern[hanging=true,waterlogged=false]")
            d.set(l1, tu, z0, "lantern[hanging=true,waterlogged=false]")


def make_doors(d, pack, L):
    M = MATS[pack]
    for (x, z, deck, kind) in level_doors(pack, L):
        fy, top = LV[deck]
        y = fy + 1
        ns = d.air(x, y, z - 1) or "substitution" in d.get(x, y, z - 1)
        ss = d.air(x, y, z + 1) or "substitution" in d.get(x, y, z + 1)
        along_x_wall = ns and ss
        d.set(x, fy, z, M["floor"]["corr"])
        if kind == "door":
            d.door(x, y, z, "south" if along_x_wall else "east", M["door"])
        else:
            d.set(x, y, z, AIR)
            d.set(x, y + 1, z, AIR)
        if kind == "vault":
            frame = {"Neoterra": "iron_block", "Hearthwood": "chiseled_stone_bricks",
                     "Cascadia": "spruce_log[axis=y]"}[pack]
            side = [(1, 0), (-1, 0)] if along_x_wall else [(0, 1), (0, -1)]
            for dx, dz in side:
                for yy in range(y, y + 3):
                    if not d.air(x + dx, yy, z + dz) and "door" not in d.get(x + dx, yy, z + dz):
                        d.set(x + dx, yy, z + dz, frame)
            if not d.air(x, y + 2, z):
                d.set(x, y + 2, z, frame if pack != "Cascadia" else
                      "spruce_log[axis=%s]" % ("x" if along_x_wall else "z"))


# ---------------------------------------------------------------------------------------------------- generic rooms
POTS = ["decorated_pot[cracked=false,facing=north,waterlogged=false]", "potted_fern",
        "candle[candles=3,lit=false,waterlogged=false]", "potted_azure_bluet", "lantern[hanging=false,waterlogged=false]",
        "potted_bamboo", "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]"]


def w_recipe(name, d, x, y, z, fac, pack, M, i, top):
    wood = M["wood"]
    if name == "crate":
        d.set(x, y, z, f"barrel[facing={fac},open=false]")
        if i % 2:
            d.set(x, y + 1, z, "barrel[facing=up,open=false]")
    elif name == "sacks":
        d.set(x, y, z, {"Neoterra": "light_gray_wool", "Hearthwood": "white_wool", "Cascadia": "brown_wool"}[pack])
        d.set(x, y + 1, z, {"Neoterra": "light_gray_carpet", "Hearthwood": "white_carpet",
                            "Cascadia": "brown_carpet"}[pack])
    elif name == "shelf":
        d.set(x, y, z, slab(M["slab"]))
        d.set(x, y + 1, z, POTS[(i + x + z) % len(POTS)])
    elif name == "counter":
        d.set(x, y, z, M["counter"] if pack != "Neoterra" else "smooth_quartz")
        d.set(x, y + 1, z, "candle[candles=2,lit=false,waterlogged=false]" if i % 2 else POTS[i % 4])
    elif name == "books":
        d.set(x, y, z, "bookshelf")
        d.set(x, y + 1, z, "bookshelf")
    elif name == "chis":
        d.set(x, y, z, chiseled(fac, i))
        d.set(x, y + 1, z, chiseled(fac, i + 3))
    elif name == "console":
        if pack == "Neoterra":
            d.set(x, y, z, "polished_andesite")
            d.set(x, y + 1, z, "redstone_lamp[lit=true]" if i % 2 else "black_stained_glass")
        elif pack == "Hearthwood":
            d.set(x, y, z, f"lectern[facing={fac},has_book=true,powered=false]")
        else:
            d.set(x, y, z, "spruce_planks")
            d.set(x, y + 1, z, "lantern[hanging=false,waterlogged=false]" if i % 2 else "potted_dead_bush")
    elif name == "map":
        d.set(x, y, z, "cartography_table")
    elif name == "machine":
        if pack == "Neoterra":
            d.set(x, y, z, "copper_block" if i % 2 else "cut_copper")
            d.set(x, y + 1, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        elif pack == "Hearthwood":
            d.set(x, y, z, "bricks")
            d.set(x, y + 1, z, "copper_block")
        else:
            d.set(x, y, z, "iron_block")
            d.set(x, y + 1, z, "iron_bars")
    elif name == "tank":
        d.set(x, y, z, "light_blue_stained_glass")
        d.set(x, y + 1, z, "light_blue_stained_glass")
    elif name == "weapons":
        d.set(x, y, z, f"{wood}_fence")
        d.set(x, y + 1, z, trap(wood, fac, "top", True))
    elif name == "target":
        d.set(x, y, z, "hay_block[axis=y]")
        d.set(x, y + 1, z, "target[power=0]")
    elif name == "bench":
        d.chair(x, y, z, OPP[fac], wood, sit=False)
    elif name == "cauldron":
        d.set(x, y, z, "water_cauldron[level=3]")
    elif name == "brew":
        d.set(x, y, z, slab(M["slab"]))
        d.set(x, y + 1, z, "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]")
    elif name == "loom":
        d.set(x, y, z, f"loom[facing={fac}]")
    elif name == "anvil":
        d.set(x, y, z, f"anvil[facing={CW[fac]}]")
    elif name == "grind":
        d.set(x, y, z, f"grindstone[face=floor,facing={fac}]")
    elif name == "plant":
        d.set(x, y, z, M["plant"])
    elif name == "locker":
        mat = {"Neoterra": "light_gray_concrete", "Hearthwood": "dark_oak_planks", "Cascadia": "spruce_planks"}[pack]
        d.set(x, y, z, mat)
        d.set(x, y + 1, z, mat)
        tr = "iron_trapdoor" if pack == "Neoterra" else f"{wood}_trapdoor"
        if i % 2 == 0 and top >= y + 2:
            d.set(x, y + 2, z, f"{tr}[facing={fac},half=bottom,open=false,powered=false,waterlogged=false]")
    elif name == "bed":
        dx, dz = D4[fac]
        if d.air(x + dx, y, z + dz):
            d.bed(x, y, z, OPP[fac], M["bed"])
            d.placed["beds"] -= 1                   # extra bunks don't count towards the hut's beds
        else:
            d.set(x, y, z, slab(M["slab"]))
    elif name == "radio":
        d.set(x, y, z, "note_block[instrument=harp,note=0,powered=false]")
        d.set(x, y + 1, z, "jukebox[has_record=false]" if pack != "Neoterra" else "redstone_lamp[lit=true]")


def c_recipe(name, d, x, y, z, pack, M, i, top):
    wood = M["wood"]
    if name == "table4":
        d.table(x, y, z, wood, "post")
        for s_, (dx, dz) in D4.items():
            d.chair(x + dx, y, z + dz, s_, wood, sit=False)
    elif name == "desk":
        d.table(x, y, z, wood, "slab", M["slab"])
        d.set(x, y + 1, z, "lantern[hanging=false,waterlogged=false]" if i % 2 else "candle[candles=1,lit=false,"
                                                                                   "waterlogged=false]")
    elif name == "punchbag":
        if top >= y + 2:
            d.set(x, y + 1, z, "hay_block[axis=y]")
            for yy in range(y + 2, top + 1):
                d.set(x, yy, z, "chain[axis=y,waterlogged=false]")
        else:
            d.set(x, y, z, "hay_block[axis=y]")
    elif name == "tank":
        for yy in range(y, min(top, y + 2) + 1):
            d.set(x, yy, z, "light_blue_stained_glass")
        if top > y + 2:
            d.set(x, y + 3, z, "chain[axis=y,waterlogged=false]")
    elif name == "machine":
        w_recipe("machine", d, x, y, z, "north", pack, M, i, top)
        if top >= y + 3:
            d.set(x, y + 2, z, "chain[axis=y,waterlogged=false]")
    elif name == "crates":
        d.set(x, y, z, "barrel[facing=up,open=false]")
        d.set(x, y + 1, z, "barrel[facing=north,open=false]" if i % 2 else "hay_block[axis=y]")
    elif name == "planter":
        d.set(x, y, z, "moss_block")
        d.set(x, y + 1, z, "flowering_azalea" if i % 2 else "azalea")
    elif name == "labtable":
        d.set(x, y, z, M["counter"] if pack != "Neoterra" else "smooth_quartz")
        d.set(x, y + 1, z, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")


KINDS = {
    "mess": (["counter", "shelf", "crate", "counter", "plant"], "table4"),
    "canteen": (["counter", "counter", "shelf", "sacks"], "table4"),
    "radio": (["console", "radio", "console", "books", "shelf"], "desk"),
    "ops": (["console", "map", "console", "books"], "table4"),
    "office": (["books", "shelf", "locker", "books"], "desk"),
    "laundry": (["cauldron", "sacks", "loom", "sacks", "shelf"], "crates"),
    "lab": (["brew", "counter", "cauldron", "shelf"], "labtable"),
    "gym": (["bench", "target", "bench", "locker"], "punchbag"),
    "bunks": (["bed", "locker"], None),
    "store": (["crate", "sacks", "crate", "shelf"], "crates"),
    "fabrication": (["anvil", "crate", "grind", "shelf", "locker"], "machine"),
    "generator": (["machine", "console", "machine", "locker"], "machine"),
    "water": (["tank", "machine", "tank", "console"], "tank"),
    "records": (["chis", "books", "chis", "books"], "desk"),
    "power": (["machine", "console"], "machine"),
    "armory": (["weapons", "weapons", "crate", "target", "locker"], "table4"),
    "cistern": (["tank", "tank", "console"], "tank"),
    "server": (["console", "console", "locker"], "machine"),
    "reactor": (["machine", "console", "tank"], "machine"),
    "turbine": (["machine", "machine", "console"], "machine"),
    "hydro": (["shelf", "sacks", "shelf", "crate"], "planter"),
    "guard": (["locker", "console", "bench", "shelf"], "desk"),
    "watch": (["console", "bench", "shelf"], "table4"),
    "lobby": (["bench", "shelf", "plant", "bench"], "table4"),
    "briefing": (["books", "console", "shelf"], "table4"),
    "garage": (["anvil", "crate", "locker", "crate", "grind"], "crates"),
    "parlour": (["books", "shelf", "bench", "plant"], "table4"),
    "bedroom": (["bed", "shelf", "locker", "bed"], None),
    "bunkhouse": (["bed", "locker", "bed", "shelf"], "table4"),
    "smithy": (["anvil", "grind", "crate", "weapons"], "crates"),
    "hoist": (["machine", "console", "crate"], "machine"),
    "mill": (["machine", "sacks", "crate", "sacks"], "crates"),
    "cookhouse": (["counter", "cauldron", "counter", "shelf", "crate"], "table4"),
}


def f_generic(d, R, M, L, pack, kind):
    walls, center = KINDS[kind]
    protect = set(R.keep)
    for (kx, kz) in R.keep:                       # keep a path two cells deep in front of every door
        for dx, dz in D4.values():
            nx, nz = kx + dx, kz + dz
            if R.x1 < nx < R.x2 and R.z1 < nz < R.z2:
                protect.add((nx, nz))
    i = 0
    for side in ("north", "east", "south", "west"):
        cells = wallcells(R, side)
        for j, (x, z) in enumerate(cells):
            if (x, z) in protect or not d.air(x, R.y, z) or j % 4 == 3 or j in (0, len(cells) - 1):
                continue
            w_recipe(walls[i % len(walls)], d, x, R.y, z, INTO[side], pack, M, i, R.top)
            i += 1
    if not center:
        return
    big = center == "table4"
    m = 3 if big else 2
    step = 4 if big else 3
    k = 0
    for z in range(R.z1 + m, R.z2 - m + 1, step):
        for x in range(R.x1 + m, R.x2 - m + 1, step):
            cells = [(x, z)] + ([(x + dx, z + dz) for dx, dz in D4.values()] if big else [])
            if all(d.air(cx, R.y, cz) and (cx, cz) not in protect for cx, cz in cells):
                c_recipe(center, d, x, R.y, z, pack, M, k, R.top)
                k += 1


def f_chapel(d, R, M, L, pack):
    sides = door_sides(R)
    front = next(s for s in ("north", "west", "east", "south") if s not in sides and OPP[s] in sides) \
        if any(OPP[s] in sides for s in ("north", "west", "east", "south") if s not in sides) else \
        next(s for s in ("north", "west", "east", "south") if s not in sides)
    F = Frame(R, front)
    mid = F.U // 2
    for u in range(mid - 1, mid + 2):
        x, z = F.xz(u, 0)
        if free(d, R, x, z):
            d.set(x, R.y, z, M["counter"] if pack != "Neoterra" else "smooth_quartz")
            d.set(x, R.y + 1, z, "candle[candles=4,lit=false,waterlogged=false]" if u != mid else
                  ("potted_white_tulip" if pack != "Neoterra" else "end_rod[facing=up]"))
    for u in (0, F.U - 1):
        x, z = F.xz(u, 0)
        if free(d, R, x, z):
            d.set(x, R.y, z, M["plant"])
    for v in range(2, F.V - 1, 2):
        for u in range(F.U):
            if u == mid or u in (0, F.U - 1):
                continue
            x, z = F.xz(u, v)
            if free(d, R, x, z):
                d.chair(x, R.y, z, F.back, M["wood"], sit=False)
    for side in (F.left, F.right):
        for j, (x, z) in enumerate(wallcells(R, side)):
            if j % 2 == 0 and free(d, R, x, z) and d.air(x, R.y + 1, z):
                d.set(x, R.y + 1, z, f"wall_torch[facing={INTO[side]}]" if pack != "Neoterra" else
                      f"{'white'}_wall_banner[facing={INTO[side]}]" if False else f"wall_torch[facing={INTO[side]}]")


def dress(d, R, M, pack, kind=""):
    """Rugs over the free floor, notices on bare walls, plants in empty corners."""
    if kind in ("farm",):
        return
    rugs = {"Neoterra": ("light_gray_carpet", "cyan_carpet"), "Hearthwood": ("red_carpet", "brown_carpet"),
            "Cascadia": ("brown_carpet", "green_carpet")}[pack]
    for (x, z) in ((R.x1, R.z1), (R.x2, R.z1), (R.x1, R.z2), (R.x2, R.z2)):
        nb = [(x + dx, z + dz) for dx, dz in D4.values()]
        if d.air(x, R.y, z) and (x, z) not in R.keep and not any(n in R.keep for n in nb):
            d.set(x, R.y, z, M["plant"])
    x1, x2, z1, z2 = R.x1 + 1, R.x2 - 1, R.z1 + 1, R.z2 - 1
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if d.air(x, R.y, z) and not d.air(x, R.y - 1, z) and "farmland" not in d.get(x, R.y - 1, z) \
                    and "water" not in d.get(x, R.y - 1, z):
                edge = x in (x1, x2) or z in (z1, z2)
                d.set(x, R.y, z, rugs[0] if edge else rugs[1])
    n = 0
    texts = {"Neoterra": [["NOTICE", "Drill: 0800", "Masks on"], ["DECK MAP", "A: living", "B: stores"],
                          ["RATION", "ROTA"]],
             "Hearthwood": [["Psalm 46"], ["Rota", "Mon: Bread", "Tue: Stew"], ["Keep the", "lamps", "trimmed"]],
             "Cascadia": [["SAFETY", "FIRST"], ["Shift", "rota"], ["No. 3 Adit", "est. 1911"]]}[pack]
    for side in ("north", "east", "south", "west"):
        for j, (x, z) in enumerate(wallcells(R, side)):
            if j % 4 != 3 or (x, z) in R.keep:
                continue
            if d.air(x, R.y + 1, z) or "carpet" in d.get(x, R.y + 1, z):
                if not d.air(x, R.y + 1, z):
                    continue
                wood = M["wood"]
                d.sign(x, R.y + 1, z, INTO[side], texts[n % len(texts)], wood)
                n += 1


def f_workroom(d, R, M, L, pack):
    """Workshop + boiler bench: the 12 craft blocks and the furnaces / blast furnaces along the walls."""
    items = [("anvil", "a"), ("grindstone", "a"), ("smithing_table", None), ("crafting_table", None),
             ("furnace", None), ("furnace", None), ("stonecutter", None), ("fletching_table", None),
             ("loom", None), ("crafting_table", None), ("furnace", None), ("furnace", None),
             ("smithing_table", None), ("grindstone", "a"), ("anvil", "a"), ("crafting_table", None)]
    items += [("blast_furnace", None)] * (0 if L < 2 else 1 if L < 3 else 2)
    cells = []
    for s in ("north", "east", "south", "west"):
        for (x, z) in wallcells(R, s):
            if free(d, R, x, z) and (x, z) not in [c[:2] for c in cells]:
                cells.append((x, z, INTO[s]))
    if len(cells) < len(items):
        raise RuntimeError(f"workroom fits {len(cells)}/{len(items)}")
    hood = {"Neoterra": "iron_trapdoor[facing=%s,half=top,open=false,powered=false,waterlogged=false]",
            "Hearthwood": "bricks", "Cascadia": "cobblestone"}[pack]
    for (x, z, fac), (name, kind) in zip(cells, items):
        d.item(x, R.y, z, name, CW[fac] if kind else fac)
        if "furnace" in name and R.top >= R.y + 2:
            d.set(x, R.y + 2, z, hood % fac if "%" in hood else hood)
    # centre: workbench island
    cx, cz = (R.x1 + R.x2) // 2, (R.z1 + R.z2) // 2
    for dx in (-1, 0, 1):
        if free(d, R, cx + dx, cz) and R.x1 + 2 <= cx + dx <= R.x2 - 2 and R.z1 + 2 <= cz <= R.z2 - 2:
            d.set(cx + dx, R.y, cz, f"{M['wood']}_planks" if pack != "Neoterra" else "smooth_stone")
            d.set(cx + dx, R.y + 1, cz, POTS[(dx + 1) % 3] if dx else "lantern[hanging=false,waterlogged=false]")


def f_vault_all(d, R, M, L, pack, ender):
    along = "x" if R.W >= R.D else "z"
    k = next(iter(R.keep)) if R.keep else (R.x1, R.z1)
    cross = [k[0] if along == "x" else k[1]]
    return f_vault(d, R, M, L, 10 ** 6, along, cross, ender=ender, pack=pack, fill_all=True)


# ---------------------------------------------------------------------------------------------------- surface buildings
def building(d, pal, x1, z1, x2, z2, nfl, door, kinds, L, style, roof="flat", chimney=None):
    """A furnished surface building: nfl storeys of 4 (3 air), stairs in alternate corners, styled walls & roof.
    pal: wall, wall2, plinth, trim, floor, roof (stairs/slab family), gable, accent, shutter, door, glass."""
    pack = d.pack
    M = MATS[pack]
    dx_, dz_, dfac = door
    stairs_cells = set()
    for k in range(nfl):
        yf = GY + 4 * k
        for x in range(x1 + 1, x2):
            for z in range(z1 + 1, z2):
                d.set(x, yf, z, pal["floor"])
                for y in range(yf + 1, yf + 4):
                    d.set(x, y, z, AIR)
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if not (x in (x1, x2) or z in (z1, z2)):
                    continue
                corner = x in (x1, x2) and z in (z1, z2)
                along = x - x1 if z in (z1, z2) else z - z1
                post = corner or (style != "modern" and along % 4 == 0)
                if k > 0 or style == "modern":
                    d.set(x, yf, z, pal["accent"] if style == "modern" else
                          f"{pal['trim']}[axis={'x' if z in (z1, z2) else 'z'}]" if "log" in pal["trim"] else pal["trim"])
                for y in range(yf + 1, yf + 4):
                    if post:
                        b = (f"{pal['trim']}[axis=y]" if "log" in pal["trim"] or "wood" in pal["trim"]
                             else pal["trim"])
                    elif k == 0 and y == yf + 1 and style != "modern":
                        b = pal["plinth"]
                    else:
                        b = pal["wall"] if k == 0 else pal["wall2"]
                    if "log" in b and "axis" not in b:
                        b += "[axis=%s]" % ("x" if z in (z1, z2) else "z")
                    d.set(x, y, z, b)
                # windows
                n = (x2 - x1) if z in (z1, z2) else (z2 - z1)
                if 2 <= along <= n - 2 and not corner and not post and along % 2 == 1:
                    if (x, z) == (dx_, dz_) or abs((x - dx_) + (z - dz_)) <= 1 and (x == dx_ or z == dz_):
                        continue
                    ys = (yf + 1, yf + 2) if style == "modern" or k == 0 else (yf + 2,)
                    for y in ys:
                        d.set(x, y, z, pal["glass"])
                    out = (0, -1) if z == z1 else (0, 1) if z == z2 else (-1, 0) if x == x1 else (1, 0)
                    ofac = next(f for f, v in D4.items() if v == out)
                    ox, oz = x + out[0], z + out[1]
                    if not d.bp.inside(ox, ys[0], oz):
                        continue
                    if style == "modern":
                        if k > 0:
                            d.set(ox, yf + 3, oz, f"{pal['fin']}")
                    else:
                        side = (1, 0) if out[1] else (0, 1)
                        for sgn in (1, -1):
                            sx_, sz_ = ox + side[0] * sgn, oz + side[1] * sgn
                            if d.bp.inside(sx_, ys[-1], sz_) and d.air(sx_, ys[-1], sz_) and k > 0:
                                sf = next(f for f, v in D4.items() if v == (side[0] * sgn, side[1] * sgn))
                                d.set(sx_, ys[-1], sz_, f"{pal['shutter']}_trapdoor[facing={sf},half=top,open=true,"
                                                        f"powered=false,waterlogged=false]")
                        if k > 0 and d.air(ox, ys[0] - 1, oz):
                            d.set(ox, ys[0] - 1, oz, f"{pal['shutter']}_trapdoor[facing={ofac},half=top,open=false,"
                                                     f"powered=false,waterlogged=false]")
                            d.set(ox, ys[0], oz, ["potted_red_tulip", "potted_azure_bluet", "potted_allium",
                                                  "potted_oxeye_daisy"][(x + z) % 4])
    Y = GY + 4 * nfl
    # door
    d.door(dx_, SW, dz_, dfac, pal["door"])
    ox, oz = D4[dfac]
    for sgn in (1, -1):
        side = (1, 0) if ox == 0 else (0, 1)
        lx, lz = dx_ + side[0] * sgn + ox, dz_ + side[1] * sgn + oz
        if d.bp.inside(lx, SW + 2, lz):
            d.set(dx_ + side[0] * sgn, SW + 2, dz_ + side[1] * sgn,
                  pal["trim"] + ("[axis=y]" if "log" in pal["trim"] else ""))
            d.set(lx, SW + 2, lz, f"wall_torch[facing={dfac}]" if style != "modern" else f"end_rod[facing={dfac}]")
    if d.bp.inside(dx_ + ox, SW + 3, dz_ + oz):
        cano = f"{pal['roof']}_slab[type=bottom,waterlogged=false]"
        for sgn in (-1, 0, 1):
            side = (1, 0) if ox == 0 else (0, 1)
            cx, cz = dx_ + ox + side[0] * sgn, dz_ + oz + side[1] * sgn
            if d.bp.inside(cx, SW + 3, cz):
                d.set(cx, SW + 3, cz, cano)
    # stairs between storeys, in alternating corners
    for k in range(nfl - 1):
        yf = GY + 4 * k
        sx = x1 + 1 if k % 2 == 0 else x2 - 1
        rx = sx + 1 if k % 2 == 0 else sx - 1
        for i in range(4):
            z = z1 + 1 + i
            for y in range(yf + 1, yf + 1 + i):
                d.set(sx, y, z, pal["floor"])
            d.set(sx, yf + 1 + i, z, st(pal["stairs"], "north"))
            for y in range(yf + 2 + i, yf + 5 + i):
                d.set(sx, y, z, AIR)
            stairs_cells.add((sx, z, k))
            stairs_cells.add((sx, z, k + 1))
            if i < 3:
                d.set(rx, yf + 5, z, pal["rail"])
                stairs_cells.add((rx, z, k + 1))
        stairs_cells.add((rx, z1 + 1, k))
        stairs_cells.add((sx, z1 + 5, k + 1))
        stairs_cells.add((rx, z1 + 4, k + 1))
    # roof
    if roof == "flat":
        d.flat(x1, z1, x2, z2, Y, pal["roofblock"], pal["parapet"], f"{pal['roof']}_slab")
    else:
        axis = "x" if (x2 - x1) >= (z2 - z1) else "z"
        ridge = d.gable(x1, z1, x2, z2, Y, axis, f"{pal['roof']}_stairs", f"{pal['roof']}_slab", pal["gable"],
                        overhang=1)
        if chimney:
            cx, cz = chimney
            for y in range(SW, ridge + 3):
                d.set(cx, y, cz, pal.get("chimney", "bricks"))
            d.set(cx, ridge + 3, cz, f"{pal.get('chimney', 'bricks').replace('bricks', 'brick')}_slab"
                                     f"[type=bottom,waterlogged=false]" if "brick" in pal.get("chimney", "bricks")
                  else "cobblestone_slab[type=bottom,waterlogged=false]")
    # furnish each storey
    for k in range(nfl):
        yf = GY + 4 * k
        keep = {(c[0], c[1]) for c in stairs_cells if c[2] == k}
        keep.add((dx_ - ox, dz_ - oz)) if k == 0 else None
        if k == 0:
            keep.add((dx_ - 2 * ox, dz_ - 2 * oz))
        R = room(x1 + 1, z1 + 1, x2 - 1, z2 - 1, yf + 1, yf + 3, keep)
        if chimney and roof != "flat":
            pass
        kind = kinds[k % len(kinds)]
        f_generic(d, R, M, L, pack, kind)
        for (x, z) in keep:
            pass
        xs = range(x1 + 2, x2 - 1, 4)
        zs = range(z1 + 2, z2 - 1, 4)
        for x in xs:
            for z in zs:
                if d.air(x, yf + 3, z) and (x, z) not in keep:
                    d.lamp(x, yf + 3, z, "lantern")
        dress(d, R, M, pack, kind)


# ---------------------------------------------------------------------------------------------------- bunker
def bunker_common(d, pack, L):
    P = PLANS[pack]
    M = MATS[pack]
    spaces = carve_underground(d, pack, L)
    for sp in spaces:
        if sp[0] not in CHILD_KINDS and (sp[0] not in ("vault", "archive") or pack == "Cascadia"):
            ribs(d, pack, sp)
    make_ramp(d, pack, L)
    make_wells(d, pack, L)
    make_doors(d, pack, L)
    for kind in ("kitchen", "clinic", "school", "farm"):
        sp = next(s for s in P["spaces"] if s[0] == kind)
        if sp[6] > L:
            continue
        deck, (x1, z1, x2, z2), fy, top, keep, (hx, hz) = child_geom(pack, kind, L)
        d.reserve(x1, fy, z1, x2, child_box_top(deck), z2)
        d.child_hut(hx, fy + 1, hz, CHILD_PATH[kind])
    req = d.req
    barrels = 0
    first_vault = True
    for sp in spaces:
        kind, deck, x1, z1, x2, z2, _ = sp
        if kind in CHILD_KINDS:
            continue
        fy, top = LV[deck]
        R = room(x1, z1, x2, z2, fy + 1, top, keep_for(pack, L, deck, x1, z1, x2, z2))
        if kind in CORR_KINDS:
            lights(d, R, M, top + 1, 4)
            if pack == "Hearthwood" or pack == "Cascadia":
                along_x = R.W >= R.D
                mid = (z1 + z2) // 2 if along_x else (x1 + x2) // 2
                for a in (range(x1, x2 + 1) if along_x else range(z1, z2 + 1)):
                    x, z = (a, mid) if along_x else (mid, a)
                    if d.air(x, R.y, z):
                        d.set(x, R.y, z, "red_carpet" if pack == "Hearthwood" else
                              "rail[shape=%s,waterlogged=false]" % ("east_west" if along_x else "north_south"))
            continue
        if kind == "dorm":
            sides = door_sides(R)
            short = next(s for s in (["west", "east"] if R.W >= R.D else ["north", "south"]) if s not in sides)
            cells = [c for c in wallcells(R, short) if free(d, R, *c)][1:-1]
            for i, (x, z) in enumerate(cells[:4]):
                if i % 2 == 0:
                    d.item(x, R.y, z, "water_cauldron[level=3]")
                else:
                    d.set(x, R.y, z, slab(M["slab"]))
                    d.item(x, R.y + 1, z, "brewing_stand")
            got = f_dorm(d, R, M, L, req["beds"])
            if got < req["beds"]:
                raise RuntimeError(f"dorm beds {got}/{req['beds']}")
        elif kind == "common":
            f_common(d, R, M, L, pack, req["seats"], maps=True)
        elif kind == "workroom":
            f_workroom(d, R, M, L, pack)
        elif kind == "vault":
            barrels += f_vault_all(d, R, M, L, pack, ender=first_vault and
                                   req["items"].get("minecraft:ender_chest", 0) > 0)
            first_vault = False
            continue
        elif kind == "archive":
            f_archive(d, R, M, L, req["bookshelves"], req["items"].get("minecraft:chiseled_bookshelf", 0), pack)
            lights(d, R, M, top + 1, 4, skip={((x1 + x2) // 2, (z1 + z2) // 2)})
            continue
        elif kind == "pantry":
            f_pantry(d, R, M, L, pack)
        elif kind == "chapel":
            f_chapel(d, R, M, L, pack)
        else:
            f_generic(d, R, M, L, pack, kind)
        lights(d, R, M, top + 1)
        dress(d, R, M, pack, kind)
    if barrels < req["items"]["minecraft:barrel"]:
        raise RuntimeError(f"vaults hold {barrels}")
    hx, hy, hz = P["hut"]
    d.hut(hx, hy, hz, "north")
    return spaces


def tree(d, x, z, base, kind="birch", h=4):
    for y in range(base, base + h):
        d.set(x, y, z, f"{kind}_log[axis=y]")
    for dy in range(h - 2, h + 2):
        r = 2 if dy < h + 1 else 1
        for ax in range(-r, r + 1):
            for az in range(-r, r + 1):
                if abs(ax) + abs(az) <= r + (1 if r == 2 else 0) and d.bp.inside(x + ax, base + dy, z + az) \
                        and d.air(x + ax, base + dy, z + az):
                    d.set(x + ax, base + dy, z + az, f"{kind}_leaves[distance=7,persistent=true,waterlogged=false]")


def lamp_post(d, x, z, post, top="lantern[hanging=false,waterlogged=false]", h=3):
    for y in range(SW, SW + h):
        d.set(x, y, z, post)
    d.set(x, SW + h, z, top)


# ---------------------------------------------------------------------------------------------------- Neoterra
def neoterra(rel, L):
    P = PLANS["Neoterra"]
    sx, sy, sz = P["size"]
    d = Design("Neoterra", rel, (sx, sy, sz), gy=GY, paving="grass_block[snowy=false]")
    # forecourt: patterned paving
    for x in range(18, 37):
        for z in range(0, 2):
            d.set(x, GY, z, "polished_andesite" if (x + z) % 3 else "smooth_stone")
    for x in range(25, 30):
        for z in range(0, 5):
            d.set(x, GY, z, "smooth_stone" if x in (25, 29) else "polished_diorite")
    bunker_common(d, "Neoterra", L)
    # hall: reception desk + sign
    d.counter(28, 13, 31, 13, 19, body="smooth_quartz")
    d.chair(30, 19, 14, "south", "birch", sit=False)
    d.sign(25, 20, 15, "north", ["CIVIL DEFENCE", "SHELTER 07", "DECK A", "DECK B: STAIRS"], "birch",
           glow=True, color="cyan")
    # ---- portal block over the ramp
    x1, x2, z1, z2 = 22, 32, 2, 11
    top = SW + 4
    for z in range(z1, z2 + 1):
        for x in range(x1, x2 + 1):
            inner = 26 <= x <= 28 and z >= z1 + 1
            for y in range(SW, top + 1):
                if inner and y < top:
                    continue
                d.set(x, y, z, "light_gray_concrete" if y < top else "smooth_stone")
    for z in range(z1, z2 + 1):
        d.set(x1, top, z, st("stone_stairs", "east"))
        d.set(x2, top, z, st("stone_stairs", "west"))
    for y in range(SW, SW + 3):
        for x in range(26, 29):
            d.set(x, y, z1, AIR)
    for y in range(SW, SW + 4):
        for x in (25, 29):
            d.set(x, y, z1, "yellow_concrete" if (y + x) % 2 else "black_concrete")
    for x in range(25, 30):
        d.set(x, SW + 3, z1, "yellow_concrete" if x % 2 else "black_concrete")
    for z in range(z1 + 1, z2 + 1):
        d.set(27, top - 1, z, "sea_lantern" if z % 3 == 0 else "light_gray_concrete")
        for x in range(26, 29):
            for y in range(SW, top - 1):
                if z <= 4:
                    d.set(x, y, z, AIR)
    for x in range(26, 29):
        for z in range(z1 + 1, 5):
            d.set(x, GY, z, "polished_andesite")
    for x in range(29, 33):                                  # sliding blast door parked on its track
        d.set(x, GY, z1 - 1, "polished_blackstone")
        if x > 29:
            for y in range(SW, SW + 3):
                d.set(x, y, z1 - 1, "iron_block")
    d.set(31, SW + 1, z1 - 1, "heavy_core")
    for x, t in ((26, "CIVIL"), (27, "SHELTER"), (28, "DEFENCE")):
        d.sign(x, SW + 4, z1 - 1, "north", ["", t, "07" if x == 27 else ""], "birch", glow=True, color="yellow")
    for x in (23, 31):
        d.set(x, SW + 2, z1 - 1, "end_rod[facing=north]")
    for z in range(z1 + 3, z2 + 3):                          # grass berm
        for x in range(x1 - 2, x2 + 3):
            if x1 <= x <= x2 and z <= z2:
                continue
            h = 3 - max(0, (x1 - x) if x < x1 else (x - x2) if x > x2 else 0) - max(0, z - z2)
            for y in range(SW, SW + max(0, h)):
                d.set(x, y, z, "dirt" if y < SW + h - 1 else "grass_block[snowy=false]")
    d.fill(x1, top, z1 + 3, x2, top, z2, "moss_block")
    for x in (20, 34):
        lamp_post(d, x, 0, "andesite_wall", "sea_lantern", 2)
    for x in (21, 33):
        d.set(x, SW, 4, "potted_bamboo")
    if L >= 2:              # vent stacks, escape hatch, periscopes, birches, benches
        for (vx, vz) in ((12, 13), (42, 13)):
            for y in range(SW, SW + 3):
                for ax in (-1, 0, 1):
                    for az in (-1, 0, 1):
                        d.set(vx + ax, y, vz + az, "light_gray_concrete" if y < SW + 2 else "iron_bars")
            d.fill(vx - 1, SW + 3, vz - 1, vx + 1, SW + 3, vz + 1, "smooth_stone_slab[type=bottom,waterlogged=false]")
        for ax in (-1, 0, 1):
            for az in (-1, 0, 1):
                d.set(6 + ax, GY, 22 + az, "light_gray_concrete")
        d.set(6, SW, 22, "iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
        for (tx, tz) in ((3, 4), (51, 4), (14, 20), (40, 20), (24, 22)):
            tree(d, tx, tz, SW, "birch")
        for (px, pz) in ((18, 18), (36, 18)):
            d.set(px, SW, pz, "andesite_wall")
            d.set(px, SW + 1, pz, "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
        for x in (19, 35):
            d.chair(x, SW, 3, "west" if x < 27 else "east", "birch", sit=False)
    if L >= 3:              # guardhouse (grey concrete + orange band, quartz parapet)
        pal = dict(wall="light_gray_concrete", wall2="white_concrete", plinth="gray_concrete", trim="gray_concrete",
                   floor="polished_andesite", roof="smooth_quartz", roofblock="smooth_quartz",
                   parapet="light_gray_concrete", accent="orange_terracotta", fin="orange_concrete",
                   glass="light_gray_stained_glass_pane", door="birch", stairs="polished_andesite_stairs",
                   rail="birch_fence", shutter="birch")
        building(d, pal, 38, 3, 46, 11, 2, (42, 3, "north"), ["guard", "watch"], L, "modern")
        lamp_post(d, 37, 1, "andesite_wall", "sea_lantern", 2)
        d.set(44, SW + 9, 7, "redstone_lamp[lit=true]")
        d.fill(47, GY, 2, 52, GY, 12, "smooth_stone")
        for z in range(3, 12, 2):
            d.set(50, SW, z, "yellow_concrete") if False else d.set(50, GY, z, "yellow_concrete")
    if L >= 4:              # motor depot (dark grey + cyan panels, copper roof) and comms hut (mangrove cladding)
        pal = dict(wall="gray_concrete", wall2="gray_concrete", plinth="polished_blackstone", trim="polished_blackstone",
                   floor="smooth_stone", roof="cut_copper", roofblock="cut_copper", parapet="gray_concrete",
                   accent="cyan_terracotta", fin="cyan_concrete", glass="glass_pane", door="mangrove",
                   stairs="polished_blackstone_stairs", rail="iron_bars", shutter="iron")
        building(d, pal, 3, 30, 19, 42, 2, (11, 30, "north"), ["garage", "store"], L, "modern")
        d.fill(3, GY, 26, 19, GY, 29, "polished_andesite")
        for x in range(4, 19, 3):
            d.set(x, GY, 27, "yellow_concrete")
        pal2 = dict(wall="mangrove_planks", wall2="white_terracotta", plinth="deepslate_tiles", trim="deepslate_tiles",
                    floor="mangrove_planks", roof="deepslate_tile", roofblock="deepslate_tiles",
                    parapet="deepslate_tiles", accent="magenta_terracotta", fin="magenta_concrete",
                    glass="glass_pane", door="mangrove", stairs="mangrove_stairs", rail="mangrove_fence",
                    shutter="mangrove")
        building(d, pal2, 3, 3, 11, 11, 2, (7, 11, "south"), ["radio", "office"], L, "modern")
        for x in range(0, sx):                               # perimeter fence with gaps for the gates
            if 18 <= x <= 36:
                continue
            d.set(x, SW, sz - 1, "iron_bars")
        for z in range(14, sz):
            d.set(0, SW, z, "iron_bars")
            d.set(sx - 1, SW, z, "iron_bars")
    if L >= 5:              # HQ: white concrete & glass, lime fins, green roof, radio mast
        pal = dict(wall="white_concrete", wall2="white_concrete", plinth="polished_blackstone", trim="quartz_block",
                   floor="polished_diorite", roof="smooth_quartz", roofblock="moss_block", parapet="white_concrete",
                   accent="lime_terracotta", fin="lime_concrete", glass="glass_pane", door="birch",
                   stairs="smooth_quartz_stairs", rail="birch_fence", shutter="birch")
        building(d, pal, 32, 32, 50, 48, 5, (41, 32, "north"), ["lobby", "briefing", "office", "ops", "radio"], L,
                 "modern")
        pal3 = dict(wall="white_terracotta", wall2="brown_terracotta", plinth="polished_deepslate",
                    trim="polished_deepslate", floor="birch_planks", roof="deepslate_tile", roofblock="deepslate_tiles",
                    parapet="polished_deepslate", accent="yellow_terracotta", fin="yellow_concrete",
                    glass="glass_pane", door="cherry", stairs="birch_stairs", rail="birch_fence", shutter="cherry")
        building(d, pal3, 3, 45, 17, 53, 2, (10, 45, "north"), ["bunkhouse", "canteen"], L, "modern")
        for x in range(4, 17, 3):
            d.set(x, SW, 44, "potted_bamboo" if x % 2 else "andesite_wall")
        # water tower
        wx, wz = 24, 47
        for y in range(SW, SW + 7):
            for (ax, az) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                d.set(wx + ax, y, wz + az, "andesite_wall")
        for y in range(SW + 7, SW + 10):
            for ax in (-2, -1, 0, 1, 2):
                for az in (-2, -1, 0, 1, 2):
                    if abs(ax) == 2 or abs(az) == 2:
                        d.set(wx + ax, y, wz + az, "light_gray_concrete" if y != SW + 8 else "cyan_terracotta")
        d.fill(wx - 2, SW + 10, wz - 2, wx + 2, SW + 10, wz + 2, "smooth_quartz_slab[type=bottom,waterlogged=false]")
        d.fill(30, GY, 28, 52, GY, 31, "polished_diorite")
        for x in range(31, 52, 4):
            d.set(x, SW, 29, "potted_bamboo")
            lamp_post(d, x + 2, 28, "andesite_wall", "sea_lantern", 2)
        mx, mz = 47, 45
        for y in range(GY + 21, GY + 28):
            d.set(mx, y, mz, "iron_bars" if y % 3 else "andesite_wall")
        d.set(mx, GY + 28, mz, "redstone_lamp[lit=true]")
        d.set(mx, GY + 29, mz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        for x in range(34, 45, 3):
            d.set(x, GY + 21, 46, "daylight_detector[inverted=false,power=0]")
    return d


# ---------------------------------------------------------------------------------------------------- Hearthwood
def hedge(d, x1, z1, x2, z2, gaps=()):
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if (x, z) not in gaps and d.air(x, SW, z):
                d.set(x, SW, z, "oak_leaves[distance=7,persistent=true,waterlogged=false]")


def flowerbed(d, x1, z1, x2, z2, salt=0):
    fl = ["poppy", "dandelion", "azure_bluet", "oxeye_daisy", "cornflower", "allium", "pink_tulip", "lily_of_the_valley"]
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            d.set(x, GY, z, "grass_block[snowy=false]")
            if d.air(x, SW, z):
                d.set(x, SW, z, fl[(x * 3 + z + salt) % len(fl)])


def hearthwood(rel, L):
    P = PLANS["Hearthwood"]
    sx, sy, sz = P["size"]
    d = Design("Hearthwood", rel, (sx, sy, sz), gy=GY, paving="grass_block[snowy=false]")
    bunker_common(d, "Hearthwood", L)
    x0, w, zf = P["ramp"]
    # ---- ruined chapel round the cellar steps
    cx1, cx2, cz1, cz2 = 22, 32, 0, 13
    for z in range(cz1, cz2 + 1):
        for x in range(cx1, cx2 + 1):
            if x in (cx1, cx2) or z in (cz1, cz2):
                h = 5 - (H(x, 0, z) % 4)
                if z == cz2:
                    h = 2 + H(x, 1, z) % 3
                if x == cx2 and z > 7:
                    h = 1 + H(x, 2, z) % 2
                for y in range(SW, SW + h):
                    d.set(x, y, z, wall_block("Hearthwood", x, y, z, -1))
    for x in range(cx1, cx2 + 1, 4):                             # buttresses
        for y in range(SW, SW + 3):
            if cz1 + 1 <= cz2 and d.bp.inside(x, y, cz2 + 1):
                d.set(x, y, cz2 + 1, "stone_bricks" if y < SW + 2 else st("stone_brick_stairs", "north"))
    for z in range(cz1 + 1, cz2):
        for x in range(cx1 + 1, cx2):
            d.set(x, GY, z, "mossy_stone_bricks" if H(x, 3, z) < 30 else "stone_bricks")
    # west gable with doorway and broken lancet
    gx = (cx1 + cx2) // 2
    for y in range(SW, SW + 8):
        d.set(gx - 2, y, cz1, "stone_bricks")
        d.set(gx + 2, y, cz1, "stone_bricks")
    for y in range(SW, SW + 3):
        for x in (gx - 1, gx, gx + 1):
            d.set(x, y, cz1, AIR)
    d.set(gx - 1, SW + 3, cz1, st("stone_brick_stairs", "east", "top"))
    d.set(gx + 1, SW + 3, cz1, st("stone_brick_stairs", "west", "top"))
    d.set(gx, SW + 3, cz1, "chiseled_stone_bricks")
    for y in range(SW + 4, SW + 7):
        d.set(gx - 1, y, cz1, "stone_bricks")
        d.set(gx + 1, y, cz1, "stone_bricks")
        d.set(gx, y, cz1, "glass_pane" if y < SW + 6 else "stone_bricks")
    # pointed arch over the cellar steps
    for y in range(SW, SW + 3):
        d.set(x0 - 1, y, zf, "stone_bricks")
        d.set(x0 + w, y, zf, "stone_bricks")
    for x in range(x0, x0 + w):
        d.set(x, SW + 3, zf, "stone_bricks")
    d.set(x0, SW + 3, zf, st("stone_brick_stairs", "east", "top"))
    d.set(x0 + w - 1, SW + 3, zf, st("stone_brick_stairs", "west", "top"))
    d.set(x0 - 1, SW + 3, zf, "stone_bricks")
    d.set(x0 + w, SW + 3, zf, "stone_bricks")
    d.set(x0 + 1, SW + 4, zf, "chiseled_stone_bricks")
    for z in range(zf + 1, zf + 6):
        d.set(x0 - 1, SW, z, "stone_brick_wall")
        d.set(x0 + w, SW, z, "stone_brick_wall")
    d.set(x0 + w, SW + 1, zf + 2, "lantern[hanging=false,waterlogged=false]")
    d.set(x0 - 1, SW + 1, zf + 4, "lantern[hanging=false,waterlogged=false]")
    for (x, z) in ((23, 2), (31, 3), (24, 11), (31, 11)):
        if d.air(x, SW, z):
            d.set(x, SW, z, "fern" if (x + z) % 2 else "sweet_berry_bush[age=1]")
    # gravel lane and front gardens
    for z in range(0, sz):
        d.set(36, GY, z, "gravel")
        d.set(37, GY, z, "gravel")
    for x in range(0, sx):
        d.set(x, GY, 16, "gravel")
        d.set(x, GY, 17, "gravel" if x % 5 else "cobblestone")
    flowerbed(d, 2, 1, 18, 2)
    hedge(d, 1, 4, 19, 4, gaps={(10, 4)})
    tree(d, 14, 9, SW, "dark_oak", 5)
    tree(d, 5, 10, SW, "oak", 4)
    for x in (34, 39):
        lamp_post(d, x, 15, "dark_oak_fence", "lantern[hanging=false,waterlogged=false]", 3)
    d.chair(20, SW, 14, "north", "dark_oak", sit=False)
    d.chair(21, SW, 14, "north", "dark_oak", sit=False)
    if L >= 2:              # the garden well (air shaft cap), vegetable patch, hedges
        wx, wz = 44, 20
        for ax in (-1, 0, 1):
            for az in (-1, 0, 1):
                if (ax, az) != (0, 0):
                    d.set(wx + ax, SW, wz + az, "mossy_cobblestone" if (ax + az) % 2 else "cobblestone")
        d.set(wx, SW, wz, "iron_bars")
        for ax in (-1, 1):
            d.set(wx + ax, SW + 1, wz, "oak_fence")
            d.set(wx + ax, SW + 2, wz, "oak_fence")
        for ax in (-1, 0, 1):
            d.set(wx + ax, SW + 3, wz, "mud_brick_slab[type=bottom,waterlogged=false]")
        d.set(wx, SW + 2, wz, "chain[axis=y,waterlogged=false]")
        for x in range(40, 52):
            for z in range(23, 29):
                if x in (40, 51) or z in (23, 28):
                    d.set(x, SW, z, "oak_fence")
                elif z == 25:
                    d.set(x, GY, z, "water")
                else:
                    d.set(x, GY, z, "farmland[moisture=7]")
                    d.set(x, SW, z, ["carrots[age=5]", "potatoes[age=6]", "beetroots[age=2]", "wheat[age=6]"][x % 4])
        d.set(45, SW, 23, "oak_fence_gate[facing=north,in_wall=false,open=false,powered=false]")
        for (tx, tz) in ((55, 4), (58, 12), (3, 24)):
            tree(d, tx, tz, SW, "oak", 4)
    if L >= 3:              # gardener's cottage: brick ground floor, white plaster & dark oak above, slate roof
        pal = dict(wall="bricks", wall2="calcite", plinth="stone_bricks", trim="stripped_dark_oak_log",
                   floor="spruce_planks", roof="deepslate_tile", gable="calcite", accent="dark_oak_planks",
                   glass="glass_pane", door="warped", stairs="spruce_stairs", rail="dark_oak_fence",
                   shutter="warped", chimney="bricks")
        building(d, pal, 40, 3, 50, 11, 2, (45, 11, "south"), ["parlour", "bedroom"], L, "tudor", "gable",
                 chimney=(51, 7))
        flowerbed(d, 41, 12, 44, 13, 1)
        flowerbed(d, 47, 12, 50, 13, 2)
        for x in range(39, 52):
            if x not in (45,):
                d.set(x, SW, 14, "oak_fence") if x in (39, 51) else None
    if L >= 4:              # almshouse row: Cotswold stone, red tile roof, green shutters
        pal = dict(wall="smooth_sandstone", wall2="sandstone", plinth="cut_sandstone", trim="stripped_oak_log",
                   floor="oak_planks", roof="brick", gable="smooth_sandstone", accent="oak_planks",
                   glass="glass_pane", door="mangrove", stairs="oak_stairs", rail="oak_fence", shutter="bamboo",
                   chimney="bricks")
        building(d, pal, 3, 21, 21, 29, 2, (12, 21, "north"), ["parlour", "bedroom"], L, "tudor", "gable",
                 chimney=(2, 25))
        flowerbed(d, 4, 19, 10, 19, 3)
        flowerbed(d, 14, 19, 20, 19, 4)
        for x in (3, 21):
            lamp_post(d, x, 18, "dark_oak_fence", "lantern[hanging=false,waterlogged=false]", 3)
    if L >= 4:              # smithy: stone and oak frame, spruce shingles, yellow shutters
        pal = dict(wall="stone_bricks", wall2="stone_bricks", plinth="cobblestone", trim="stripped_oak_log",
                   floor="cobblestone", roof="spruce", gable="oak_planks", accent="oak_planks", glass="glass_pane",
                   door="oak", stairs="oak_stairs", rail="oak_fence", shutter="bamboo", chimney="cobblestone")
        building(d, pal, 44, 46, 56, 53, 1, (50, 46, "north"), ["smithy"], L, "tudor", "gable", chimney=(57, 49))
        d.set(42, SW, 47, "anvil[facing=north]")
        d.set(42, SW, 49, "water_cauldron[level=3]")
    if L >= 5:              # vicarage: light-blue colour-washed walls, rose granite roof, red door
        pal = dict(wall="light_blue_terracotta", wall2="white_terracotta", plinth="stone_bricks",
                   trim="stripped_dark_oak_log", floor="oak_planks", roof="granite", gable="white_terracotta",
                   accent="dark_oak_planks", glass="glass_pane", door="crimson", stairs="dark_oak_stairs",
                   rail="dark_oak_fence", shutter="warped", chimney="bricks")
        building(d, pal, 3, 41, 15, 51, 2, (9, 41, "north"), ["parlour", "bedroom"], L, "tudor", "gable",
                 chimney=(2, 46))
        flowerbed(d, 3, 39, 7, 39, 5)
        flowerbed(d, 11, 39, 15, 39, 6)
    if L >= 5:              # tithe barn (mud brick and oak frame, brown tile roof) and the bell tower
        pal = dict(wall="mud_bricks", wall2="white_terracotta", plinth="cobblestone", trim="stripped_oak_log",
                   floor="spruce_planks", roof="mud_brick", gable="white_terracotta", accent="oak_planks",
                   glass="glass_pane", door="crimson", stairs="spruce_stairs", rail="spruce_fence",
                   shutter="crimson", chimney="cobblestone")
        building(d, pal, 40, 32, 56, 42, 2, (48, 32, "north"), ["store", "bunkhouse"], L, "tudor", "gable")
        tx, tz = 6, 34
        for y in range(SW, SW + 16):
            for ax in range(0, 5):
                for az in range(0, 5):
                    if ax in (0, 4) or az in (0, 4):
                        b = "stone_bricks" if (ax in (0, 4) and az in (0, 4)) else wall_block("Hearthwood", tx + ax, y,
                                                                                         tz + az, -1)
                        if y in (SW + 12, SW + 13) and 1 <= ax <= 3 and az in (0, 4):
                            b = AIR if ax == 2 else b
                        if y in (SW + 12, SW + 13) and 1 <= az <= 3 and ax in (0, 4):
                            b = AIR if az == 2 else b
                        d.set(tx + ax, y, tz + az, b)
        d.set(tx + 2, SW, tz, AIR)
        d.set(tx + 2, SW + 1, tz, AIR)
        d.door(tx + 2, SW, tz, "north", "dark_oak")
        d.set(tx + 2, SW + 12, tz + 2, "bell[attachment=ceiling,facing=north,powered=false]")
        d.hip(tx, tz, tx + 4, tz + 4, SW + 16, "deepslate_tile_stairs", "deepslate_tile_slab", overhang=1)
        d.set(tx + 2, SW + 15, tz + 2, "dark_oak_planks")
        d.set(tx + 2, SW + 3, tz + 2, "lantern[hanging=false,waterlogged=false]")
        d.set(tx + 2, SW + 2, tz + 2, "dark_oak_planks")
    return d


# ---------------------------------------------------------------------------------------------------- Cascadia
def cascadia(rel, L):
    P = PLANS["Cascadia"]
    sx, sy, sz = P["size"]
    d = Design("Cascadia", rel, (sx, sy, sz), gy=GY, paving="grass_block[snowy=false]")
    bunker_common(d, "Cascadia", L)
    x0, w, zf = P["ramp"]
    # ---- rock knoll: a skin of rock, moss and turf over an earth core (substitution)
    knoll = {}
    for x in range(14, 41):
        for z in range(8, 36):
            fx = (x - 27) / 13.5
            fz = (z - 21) / 13.0
            h = 8.0 * (1 - fx * fx - fz * fz) + (H(x, 0, z) % 3) - 1
            if z < 11:
                h = min(h, (z - 7) * 2)
            h = int(h)
            if h > 0:
                knoll[(x, z)] = h
    for (x, z), h in knoll.items():
        for y in range(SW, SW + h):
            outer = y >= SW + h - 2 or any(knoll.get((x + ax, z + az), 0) <= y - SW for ax, az in D4.values())
            if not outer:
                d.set(x, y, z, SOLID)
                continue
            top_ = y == SW + h - 1
            hh = H(x, y, z, 5)
            if top_ and z > 11:
                b = "grass_block[snowy=false]" if hh < 60 else "moss_block" if hh < 80 else "coarse_dirt"
            else:
                b = wall_block("Cascadia", x, y, z, -1)
            d.set(x, y, z, b)
    # adit: timbered tunnel into the rock face, then the incline
    for z in range(3, zf):
        for x in range(x0 - 1, x0 + w + 1):
            for y in range(SW, SW + 4):
                inner = x0 <= x < x0 + w and y < SW + 3
                d.set(x, y, z, AIR if inner else wall_block("Cascadia", x, y, z, -1))
        for x in range(x0, x0 + w):
            d.set(x, GY, z, "gravel")
    for z in range(3, zf, 2):
        for y in range(SW, SW + 3):
            d.set(x0 - 1, y, z, "spruce_log[axis=y]")
            d.set(x0 + w, y, z, "spruce_log[axis=y]")
        for x in range(x0 - 1, x0 + w + 1):
            d.set(x, SW + 3, z, "spruce_log[axis=x]")
    for z in range(zf, zf + 6):
        for x in (x0 - 1, x0 + w):
            for y in range(SW, SW + 4):
                d.set(x, y, z, wall_block("Cascadia", x, y, z, -1))
        for x in range(x0, x0 + w):
            d.set(x, SW + 3, z, "spruce_planks")
    pz = 2
    for y in range(SW, SW + 4):
        d.set(x0 - 1, y, pz, "spruce_log[axis=y]")
        d.set(x0 + w, y, pz, "spruce_log[axis=y]")
    for x in range(x0 - 2, x0 + w + 2):
        d.set(x, SW + 4, pz, "spruce_log[axis=x]")
        d.set(x, SW + 5, pz, "spruce_slab[type=bottom,waterlogged=false]")
    for x in range(x0, x0 + w):
        d.set(x, SW + 3, pz, "spruce_slab[type=top,waterlogged=false]")
    d.sign(x0 + 1, SW + 4, pz - 1, "north", ["RIDGE", "REFUGE", "~ No. 3 Adit ~"], "spruce")
    d.set(x0 - 1, SW + 3, pz - 1, "lantern[hanging=true,waterlogged=false]")
    d.set(x0 + w, SW + 3, pz - 1, "lantern[hanging=true,waterlogged=false]")
    for z in range(0, zf):
        d.set(x0 + 1, SW, z, "rail[shape=north_south,waterlogged=false]")
        d.set(x0 + 1, GY, z, "gravel")
    for (tx, tz) in ((22, 18), (33, 20), (26, 27), (31, 14)):
        h = knoll.get((tx, tz))
        if h:
            tree(d, tx, tz, SW + h, "spruce", 5)
    # woodpile and yard
    for x in range(17, 23):
        d.set(x, SW, 1, "spruce_log[axis=x]")
        if x % 2:
            d.set(x, SW + 1, 1, "spruce_log[axis=x]")
    for x in range(0, 14):
        d.set(x, SW, 0, "spruce_fence") if x % 6 else None
    d.set(24, SW, 1, "water_cauldron[level=3]")
    if L >= 2:              # ore carts, lamp posts, a split-rail fence
        for (cx, cz) in ((x0 + 1, 0),):
            d.set(cx + 2, SW, cz, "barrel[facing=up,open=false]")
        for x in (x0 - 3, x0 + w + 2):
            lamp_post(d, x, 1, "spruce_fence", "lantern[hanging=false,waterlogged=false]", 3)
        for z in range(14, 40):
            d.set(44, SW, z, "spruce_fence") if z % 4 else None
        tree(d, 48, 50, SW, "spruce", 6)
        tree(d, 6, 50, SW, "spruce", 6)
    if L >= 3:              # bunkhouse: log walls, dark shake roof, red shutters
        pal = dict(wall="spruce_log", wall2="spruce_log", plinth="cobblestone", trim="stripped_spruce_log",
                   floor="spruce_planks", roof="cobbled_deepslate", gable="spruce_planks", accent="spruce_planks",
                   glass="glass_pane", door="mangrove", stairs="spruce_stairs", rail="spruce_fence",
                   shutter="mangrove", chimney="cobblestone")
        building(d, pal, 2, 3, 12, 13, 2, (7, 3, "north"), ["bunkhouse", "bunkhouse"], L, "timber", "gable",
                 chimney=(1, 8))
        for x in range(3, 12):
            d.set(x, GY, 2, "spruce_planks")
            d.set(x, GY, 1, "spruce_planks")
        for x in (3, 11):
            for y in range(SW, SW + 3):
                d.set(x, y, 1, "spruce_log[axis=y]")
            d.set(x, SW + 3, 1, "spruce_slab[type=bottom,waterlogged=false]")
        for x in range(4, 11):
            d.set(x, SW + 3, 1, "spruce_slab[type=bottom,waterlogged=false]")
        d.chair(4, SW, 2, "south", "spruce", sit=False)
    if L >= 4:              # cookhouse: red mangrove siding, river-rock plinth, green-blue metal roof
        pal = dict(wall="mangrove_planks", wall2="mangrove_planks", plinth="mossy_cobblestone", trim="dark_oak_log",
                   floor="spruce_planks", roof="dark_prismarine", gable="mangrove_planks", accent="green_terracotta",
                   glass="glass_pane", door="spruce", stairs="spruce_stairs", rail="spruce_fence", shutter="spruce",
                   chimney="cobblestone")
        building(d, pal, 42, 2, 53, 12, 1, (47, 2, "north"), ["cookhouse"], L, "timber", "gable", chimney=(54, 7))
        # headframe over the old shaft: timber A-frame with sheave
        hx, hz = 47, 22
        for y in range(SW, SW + 12):
            for (ax, az) in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
                d.set(hx + ax, y, hz + az, "spruce_log[axis=y]")
            if y % 4 == 0:
                for a in range(-2, 3):
                    for (ax, az) in ((a, -2), (a, 2), (-2, a), (2, a)):
                        d.set(hx + ax, y, hz + az, "spruce_planks")
        for a in range(-2, 3):
            d.set(hx + a, SW + 12, hz, "spruce_log[axis=x]")
        d.set(hx, SW + 13, hz, "lantern[hanging=false,waterlogged=false]")
        for y in range(SW, SW + 12):
            d.set(hx, y, hz, "chain[axis=y,waterlogged=false]")
        d.set(hx, GY, hz, "cobblestone")
    if L >= 4:              # hoist house by the headframe: dark oak, slate roof, mustard trim
        pal = dict(wall="dark_oak_planks", wall2="dark_oak_planks", plinth="andesite", trim="stripped_spruce_log",
                   floor="spruce_planks", roof="deepslate_tile", gable="dark_oak_planks", accent="yellow_terracotta",
                   glass="glass_pane", door="spruce", stairs="spruce_stairs", rail="spruce_fence", shutter="spruce",
                   chimney="cobblestone")
        building(d, pal, 42, 27, 52, 35, 1, (47, 27, "north"), ["hoist"], L, "timber", "gable")
    if L >= 5:              # general store & assay office: rose cherry siding, red cedar roof, green trim
        pal = dict(wall="cherry_planks", wall2="stripped_spruce_log", plinth="mossy_cobblestone",
                   trim="spruce_log", floor="spruce_planks", roof="mangrove", gable="cherry_planks",
                   accent="green_terracotta", glass="glass_pane", door="spruce", stairs="spruce_stairs",
                   rail="spruce_fence", shutter="spruce", chimney="cobblestone")
        building(d, pal, 38, 44, 52, 56, 2, (45, 44, "north"), ["store", "office"], L, "timber", "gable",
                 chimney=(53, 50))
        for x in range(38, 53):
            d.set(x, GY, 42, "spruce_planks")
            d.set(x, GY, 43, "spruce_planks")
        for x in (38, 52):
            lamp_post(d, x, 41, "spruce_fence", "lantern[hanging=false,waterlogged=false]", 3)
    if L >= 5:              # stamp mill: pale birch boards, spruce frame, spruce roof, mustard trim; lookout
        pal = dict(wall="birch_planks", wall2="stripped_birch_log", plinth="tuff", trim="spruce_log",
                   floor="spruce_planks", roof="spruce", gable="birch_planks", accent="yellow_terracotta",
                   glass="glass_pane", door="spruce", stairs="spruce_stairs", rail="spruce_fence",
                   shutter="bamboo", chimney="cobblestone")
        building(d, pal, 2, 42, 16, 54, 2, (9, 42, "north"), ["mill", "hoist"], L, "timber", "gable")
        top = max(knoll.values())
        tx, tz = 27, 21
        base = SW + knoll.get((tx, tz), top)
        for (px, pz) in ((tx - 1, tz - 1), (tx + 1, tz - 1), (tx - 1, tz + 1), (tx + 1, tz + 1)):
            for y in range(SW + knoll.get((px, pz), 0), base + 4):
                d.set(px, y, pz, "spruce_log[axis=y]")
        d.fill(tx - 1, base + 4, tz - 1, tx + 1, base + 4, tz + 1, "spruce_planks")
        for x in range(tx - 1, tx + 2):
            for z in (tz - 1, tz + 1):
                d.set(x, base + 5, z, "spruce_fence")
        d.set(tx, base + 5, tz, "lantern[hanging=false,waterlogged=false]")
    return d


@design("bunker")
def bunker(pack, rel, L):
    d = {"Neoterra": neoterra, "Hearthwood": hearthwood, "Cascadia": cascadia}[pack](rel, L)
    reclear_ramp(d, pack)
    return d
