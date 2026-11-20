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
# space: (kind, deck, x1, z1, x2, z2, minL)       (interior box, walls one block outside)
# door:  (x, z, deck, minL, kind)  kind: 'door' (wooden door) / 'open' (plain opening) / 'vault' (framed opening)
PLANS = {
    "Neoterra": dict(
        size=(33, 40, 33),
        ramp=(15, 3, 5),                     # x0, width, first step z  (descends south, 6 steps)
        hut=(13, 19, 14),
        well=(15, 27),
        spaces=[
            ("hall", "A", 13, 11, 19, 14, 1), ("corr", "A", 15, 15, 17, 26, 1),
            ("common", "A", 3, 4, 11, 12, 1), ("command", "A", 21, 8, 29, 13, 1), ("wash", "A", 21, 3, 29, 6, 1),
            ("clinic", "A", 3, 16, 13, 22, 1), ("school", "A", 3, 24, 13, 30, 1),
            ("kitchen", "A", 19, 16, 29, 22, 1), ("dorm", "A", 19, 24, 29, 30, 1),
            ("corr", "B", 15, 3, 17, 26, 1),
            ("archive", "B", 3, 3, 13, 14, 1), ("vault", "B", 3, 16, 13, 27, 1),
            ("workshop", "B", 19, 3, 29, 9, 1), ("generator", "B", 19, 11, 29, 15, 1),
            ("farm", "B", 19, 17, 29, 25, 2), ("pantry", "B", 19, 27, 29, 30, 2),
        ],
        doors=[(12, 12, "A", 1, "door"), (20, 12, "A", 1, "door"), (25, 7, "A", 1, "door"),
               (14, 19, "A", 1, "door"), (14, 25, "A", 1, "door"), (18, 19, "A", 1, "door"),
               (18, 25, "A", 1, "door"),
               (14, 9, "B", 1, "door"), (14, 21, "B", 1, "vault"), (18, 6, "B", 1, "door"),
               (18, 13, "B", 1, "door"), (18, 21, "B", 2, "door"), (24, 26, "B", 2, "open")],
        child_huts={"kitchen": (19, 16), "clinic": (13, 16), "school": (13, 24), "farm": (19, 17)},
        vault=dict(along="x", cross=[13]),
        vent=(31, 13),
    ),
    "Hearthwood": dict(
        size=(29, 40, 33),
        ramp=(2, 2, 4),
        hut=(4, 19, 12),
        well=(16, 14),
        spaces=[
            ("corr", "A", 2, 10, 26, 12, 1), ("corr", "A", 2, 22, 26, 24, 1), ("corr", "A", 13, 13, 14, 21, 1),
            ("common", "A", 5, 2, 13, 8, 1), ("dorm", "A", 15, 2, 26, 8, 1),
            ("clinic", "A", 2, 14, 11, 20, 1), ("kitchen", "A", 19, 14, 26, 20, 1),
            ("school", "A", 2, 26, 11, 31, 1), ("wash", "A", 13, 26, 17, 31, 1), ("command", "A", 19, 26, 26, 31, 1),
            ("corr", "B", 2, 10, 26, 12, 1), ("corr", "B", 13, 13, 14, 21, 1), ("corr", "B", 2, 22, 17, 24, 1),
            ("archive", "B", 2, 2, 17, 8, 1), ("workshop", "B", 19, 2, 26, 8, 1),
            ("generator", "B", 2, 14, 11, 20, 1), ("vault", "B", 19, 14, 26, 31, 1),
            ("farm", "B", 2, 26, 11, 31, 2), ("pantry", "B", 13, 26, 17, 31, 2),
        ],
        doors=[(9, 9, "A", 1, "door"), (20, 9, "A", 1, "door"), (12, 17, "A", 1, "door"),
               (22, 21, "A", 1, "door"), (7, 25, "A", 1, "door"), (15, 25, "A", 1, "door"),
               (22, 25, "A", 1, "door"), (15, 14, "A", 1, "open"),
               (7, 9, "B", 1, "door"), (22, 9, "B", 1, "door"), (12, 17, "B", 1, "door"),
               (18, 23, "B", 1, "vault"), (7, 25, "B", 2, "door"), (15, 25, "B", 2, "door"),
               (17, 13, "B", 1, "open")],
        child_huts={"clinic": (11, 14), "kitchen": (19, 20), "school": (6, 26), "farm": (6, 26)},
        vault=dict(along="z", cross=[23]),
        vent=None,
    ),
    "Cascadia": dict(
        size=(33, 40, 29),
        ramp=(15, 3, 9),
        hut=(19, 19, 15),
        well=(15, 19),
        spaces=[
            ("corr", "A", 2, 15, 30, 17, 1),
            ("common", "A", 2, 6, 12, 13, 1), ("kitchen", "A", 20, 7, 30, 13, 1),
            ("clinic", "A", 2, 19, 12, 25, 1), ("dorm", "A", 20, 19, 30, 26, 1),
            ("corr", "B", 2, 15, 30, 17, 1),
            ("archive", "B", 2, 4, 12, 13, 1), ("generator", "B", 14, 4, 18, 13, 1), ("vault", "B", 20, 2, 30, 13, 1),
            ("farm", "B", 2, 19, 12, 27, 2), ("pantry", "B", 14, 24, 18, 27, 2), ("school", "B", 20, 19, 30, 26, 1),
        ],
        doors=[(7, 14, "A", 1, "door"), (25, 14, "A", 1, "door"), (7, 18, "A", 1, "door"),
               (25, 18, "A", 1, "door"), (15, 18, "A", 1, "open"),
               (7, 14, "B", 1, "door"), (16, 14, "B", 1, "door"), (25, 14, "B", 1, "vault"),
               (7, 18, "B", 2, "door"), (13, 25, "B", 2, "open"), (25, 18, "B", 1, "door"),
               (16, 18, "B", 1, "open")],
        child_huts={"kitchen": (24, 13), "clinic": (6, 19), "farm": (6, 19), "school": (24, 19)},
        vault=dict(along="x", cross=[25]),
        vent=(14, 6),
    ),
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
        return "mossy_stone_bricks" if h < 14 else "cracked_stone_bricks" if h < 24 else "stone_bricks"
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
                if d.get(x, ceil_y, z) not in ("minecraft:" + KEEP.split(":")[1], AIR) and \
                        "substitution" not in d.get(x, ceil_y, z):
                    d.set(x, ceil_y, z, M["lightblock"])
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
                if "substitution" not in d.get(x, R.top + 1, z):
                    d.set(x, R.top + 1, z, M["lightblock"])
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


def f_workshop(d, R, M, L, pack, outdoor=False):
    items = [("anvil", "a"), ("grindstone", "a"), ("smithing_table", None), ("crafting_table", None),
             ("stonecutter", None), ("fletching_table", None), ("loom", None), ("crafting_table", None),
             ("smithing_table", None), ("grindstone", "a"), ("anvil", "a"), ("crafting_table", None)]
    sides = door_sides(R)
    order = [s for s in ("north", "east", "west", "south") if s not in sides]
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
            d.set(x, R.top + 1, z, "sea_lantern")
        else:
            d.lamp(x, R.top, z, "lantern")


CHILD_FN = {"kitchen": c_kitchen, "clinic": c_clinic, "school": c_school, "farm": c_farm}


def child_geom(pack, kind):
    P = PLANS[pack]
    sp = next(s for s in P["spaces"] if s[0] == kind)
    _, deck, x1, z1, x2, z2, minL = sp
    fy, top = LV[deck]
    keep = set()
    for (x, z, dk, ml, k) in P["doors"]:
        if dk != deck:
            continue
        for dx, dz in D4.values():
            if x1 <= x + dx <= x2 and z1 <= z + dz <= z2:
                keep.add((x + dx, z + dz))
    return deck, (x1, z1, x2, z2), fy, top, keep, P["child_huts"][kind]


def child_design(kind, pack, rel, L):
    deck, (x1, z1, x2, z2), fy, top, keep, (hx, hz) = child_geom(pack, kind)
    M = MATS[pack]
    W, D = x2 - x1 + 1, z2 - z1 + 1
    Hh = top + 1 - fy + 1
    d = Design(pack, rel, (W, Hh, D), gy=0, paving=M["child_floor"][kind])
    # ceiling layer (the room's own ceiling, so the blueprint covers the reserved box exactly)
    cy = Hh - 1
    for x in range(W):
        for z in range(D):
            if pack == "Hearthwood":
                c = "dark_oak_planks" if (x % 3 == 1) else "stone_bricks"
            elif pack == "Cascadia":
                c = "stripped_spruce_log[axis=x]" if z % 3 == 1 else "spruce_planks"
            else:
                c = "white_concrete"
            d.set(x, cy, z, c)
    lk = {(x - x1, z - z1) for x, z in keep}
    R = room(0, 0, W - 1, D - 1, 1, Hh - 2, lk | {(hx - x1, hz - z1)})
    d.hut(hx - x1, 1, hz - z1, "north")
    CHILD_FN[kind](d, R, M, L, pack)
    if kind != "farm":
        lights(d, R, M, cy, 4, skip=())
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


# ---------------------------------------------------------------------------------------------------- carving
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


def make_well(d, pack, L):
    """Compact U-shaped stair core from deck A (walk 19) down to deck B (walk 14)."""
    P = PLANS[pack]
    M = MATS[pack]
    x0, z0 = P["well"]
    fyB = LV["B"][0]
    for y in range(fyB, 23):
        for z in range(z0 - 1, z0 + 5):
            for x in range(x0 - 1, x0 + 3):
                put_wall(d, pack, x, y, z, fyB if y < 18 else 18)
    sol = M["solid"]
    # (x, z, stair block y or None, facing, clear from, clear to)
    l1, l2 = x0, x0 + 1
    cells = [
        (l1, z0, None, None, 19, 21),
        (l1, z0 + 1, 17, "north", 18, 21),
        (l1, z0 + 2, 16, "north", 17, 20),
        (l1, z0 + 3, 15, "north", 16, 19),
        (l2, z0 + 3, 14, "west", 15, 18),
        (l2, z0 + 2, 13, "south", 14, 17),
        (l2, z0 + 1, None, None, 14, 17),
        (l2, z0, None, None, 14, 17),
    ]
    for x in (l1, l2):
        for z in range(z0, z0 + 4):
            for y in range(fyB, 22):
                d.set(x, y, z, wall_block(pack, x, y, z, fyB) if pack != "Neoterra" else "light_gray_concrete")
    for (x, z, sy, fac, c0, c1) in cells:
        if sy is None:
            d.set(x, c0 - 1, z, M["floor"]["corr"])
            for y in range(fyB, c0 - 1):
                d.set(x, y, z, sol)
        else:
            for y in range(fyB, sy):
                d.set(x, y, z, sol)
            d.set(x, sy, z, st(M["step"], fac))
        for y in range(c0, c1 + 1):
            d.set(x, y, z, AIR)
    # ceiling over deck-B landing and lamp
    for z in (z0, z0 + 1):
        d.set(l2, 18, z, M["ceil"])
    if pack == "Neoterra":
        d.set(l1, 21, z0 + 3, "sea_lantern") if not d.air(l1, 21, z0 + 3) else None
        d.set(l2 + 1, 16, z0 + 1, "sea_lantern")
    else:
        d.set(l2, 17, z0 + 1, "lantern[hanging=true,waterlogged=false]")
        if not d.air(l1, 21, z0):
            pass
        d.set(l1, 21, z0, "lantern[hanging=true,waterlogged=false]")


def make_doors(d, pack, L):
    P = PLANS[pack]
    M = MATS[pack]
    for (x, z, deck, ml, kind) in P["doors"]:
        if ml > L:
            continue
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
            frame = {"Neoterra": "iron_block", "Hearthwood": "chiseled_stone_bricks", "Cascadia": "spruce_log[axis=y]"}[pack]
            side = [(1, 0), (-1, 0)] if along_x_wall else [(0, 1), (0, -1)]
            for dx, dz in side:
                for yy in range(y, y + 3):
                    if not d.air(x + dx, yy, z + dz):
                        d.set(x + dx, yy, z + dz, frame)
            if not d.air(x, y + 2, z):
                d.set(x, y + 2, z, frame if pack != "Cascadia" else "spruce_log[axis=%s]" % ("x" if along_x_wall else "z"))


# ---------------------------------------------------------------------------------------------------- bunker
def bunker_common(d, pack, L):
    P = PLANS[pack]
    M = MATS[pack]
    spaces = carve_underground(d, pack, L)
    for sp in spaces:
        if sp[0] not in CHILD_KINDS and sp[0] not in ("vault", "archive"):
            ribs(d, pack, sp)
        elif sp[0] in ("vault", "archive") and pack == "Cascadia":
            ribs(d, pack, sp)
    make_ramp(d, pack, L)
    make_well(d, pack, L)
    make_doors(d, pack, L)
    # children: reserve their boxes, place their hut blocks
    for kind in ("kitchen", "clinic", "school", "farm"):
        sp = next(s for s in P["spaces"] if s[0] == kind)
        if sp[6] > L:
            continue
        deck, (x1, z1, x2, z2), fy, top, keep, (hx, hz) = child_geom(pack, kind)
        d.reserve(x1, fy, z1, x2, top + 1, z2)
        d.child_hut(hx, fy + 1, hz, CHILD_PATH[kind])
    # parent rooms
    req = d.req
    beds = req["beds"]
    for sp in spaces:
        kind, deck, x1, z1, x2, z2, _ = sp
        if kind in CHILD_KINDS:
            continue
        fy, top = LV[deck]
        keep = set()
        for (x, z, dk, ml, k) in P["doors"]:
            if dk == deck and ml <= L:
                for dx, dz in D4.values():
                    if x1 <= x + dx <= x2 and z1 <= z + dz <= z2:
                        keep.add((x + dx, z + dz))
        R = room(x1, z1, x2, z2, fy + 1, top, keep)
        if kind == "dorm":
            if pack == "Cascadia":
                # wash corner: two basins and the brewing stands (medicine shelf) on the south wall
                cells = [c for c in wallcells(R, "south")][-5:]
                for i, (x, z) in enumerate(cells):
                    if i in (0, 3):
                        d.item(x, R.y, z, "water_cauldron[level=3]")
                    elif i in (1, 4):
                        d.set(x, R.y, z, slab(M["slab"]))
                        d.item(x, R.y + 1, z, "brewing_stand")
                    else:
                        d.set(x, R.y, z, "stripped_spruce_wood[axis=y]")
                        d.set(x, R.y + 1, z, "lantern[hanging=false,waterlogged=false]")
            got = f_dorm(d, R, M, L, beds)
            if got < beds:
                raise RuntimeError(f"dorm beds {got}/{beds}")
            lights(d, R, M, top + 1)
        elif kind == "common":
            f_common(d, R, M, L, pack, req["seats"], maps=(pack == "Cascadia"))
            lights(d, R, M, top + 1)
        elif kind == "command":
            f_command(d, R, M, L, pack)
            lights(d, R, M, top + 1)
        elif kind == "wash":
            f_wash(d, R, M, L, pack)
            lights(d, R, M, top + 1)
        elif kind == "vault":
            v = P["vault"]
            f_vault(d, R, M, L, req["items"]["minecraft:barrel"], v["along"], v["cross"],
                    ender=req["items"].get("minecraft:ender_chest", 0) > 0, pack=pack)
        elif kind == "archive":
            f_archive(d, R, M, L, req["bookshelves"], req["items"].get("minecraft:chiseled_bookshelf", 0), pack)
            lights(d, R, M, top + 1, 4, skip={((x1 + x2) // 2, (z1 + z2) // 2)})
        elif kind == "workshop":
            f_workshop(d, R, M, L, pack)
            lights(d, R, M, top + 1)
        elif kind == "generator":
            f_generator(d, R, M, L, pack)
            lights(d, R, M, top + 1)
        elif kind == "pantry":
            f_pantry(d, R, M, L, pack)
            lights(d, R, M, top + 1)
        elif kind in ("corr", "hall"):
            lights(d, R, M, top + 1, 4)
    hx, hy, hz = P["hut"]
    d.hut(hx, hy, hz, "north")
    return spaces


# ---------------------------------------------------------------------------------------------------- Neoterra
def neoterra(rel, L):
    P = PLANS["Neoterra"]
    sx, sy, sz = P["size"]
    d = Design("Neoterra", rel, (sx, sy, sz), gy=GY, paving="grass_block[snowy=false]")
    # plaza and approach
    d.fill(9, GY, 0, 23, GY, 1, "smooth_stone")
    d.fill(14, GY, 0, 18, GY, 4, "smooth_stone")
    bunker_common(d, "Neoterra", L)
    M = MATS["Neoterra"]
    # ---- deck A extras: reception desk in the hall, signage
    d.counter(16, 13, 18, 13, 19, body="smooth_quartz")
    d.set(19, 19, 13, "smooth_quartz")
    d.chair(17, 19, 14, "south", "birch", sit=False)
    d.sign(16, 20, 15, "north", ["SHELTER 07", "", "DECK A  >>", "DECK B  v"], "birch") if False else None
    d.sign(14, 20, 15, "north", ["CIVIL DEFENCE", "SHELTER 07", "DECK A", "DECK B: STAIRS S"], "birch",
           glow=True, color="cyan")
    # ---- ventilation duct from the generator hall to a surface stack
    vx, vz = P["vent"]
    for y in range(14, GY + 1):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if (dx, dz) != (0, 0) and d.bp.inside(vx + dx, y, vz + dz):
                    put_wall(d, "Neoterra", vx + dx, y, vz + dz, 13)
        d.set(vx, y, vz, AIR)
    d.set(vx - 1, 15, vz, "iron_bars")
    d.set(vx - 1, 16, vz, "iron_bars")
    d.set(vx, 13, vz, "gray_concrete")
    # stack on the surface
    for y in range(SW, SW + 4):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if (dx, dz) != (0, 0):
                    d.set(vx + dx, y, vz + dz, "light_gray_concrete" if y < SW + 2 else "iron_bars")
        d.set(vx, y, vz, AIR)
    d.fill(vx - 1, SW + 4, vz - 1, vx + 1, SW + 4, vz + 1, "smooth_stone_slab[type=bottom,waterlogged=false]")
    # ---- surface portal: chunky concrete block over the ramp, open blast portal with hazard frame
    x1, x2, z1, z2 = 11, 21, 2, 11
    top = SW + 4                                         # roof slab y
    for z in range(z1, z2 + 1):
        for x in range(x1, x2 + 1):
            inner = 15 <= x <= 17 and z >= z1 + 1
            for y in range(SW, top + 1):
                if inner and y < top:
                    continue
                d.set(x, y, z, "light_gray_concrete" if y < top else "smooth_stone")
    # sloped shoulders: stepped concrete wedge down to the berm
    for x in range(x1, x2 + 1):
        dxs = min(x - x1, x2 - x)
        for z in range(z1, z2 + 1):
            if dxs == 0:
                d.set(x, top, z, st("stone_stairs", "east" if x == x1 else "west"))
                d.set(x, top - 1, z, "light_gray_concrete")
    # portal opening at the front with hazard stripes
    for y in range(SW, SW + 3):
        for x in range(15, 18):
            d.set(x, y, z1, AIR)
    for y in range(SW, SW + 4):
        for x in (14, 18):
            d.set(x, y, z1, "yellow_concrete" if (y + x) % 2 else "black_concrete")
    for x in range(14, 19):
        d.set(x, SW + 3, z1, "yellow_concrete" if x % 2 else "black_concrete")
    # interior: vestibule and ramp ceiling lights
    for z in range(z1 + 1, z2 + 1):
        d.set(16, top - 1, z, "sea_lantern" if z % 3 == 0 else "light_gray_concrete")
        for x in range(15, 18):
            for y in range(SW, top - 1):
                if z <= 4:
                    d.set(x, y, z, AIR)
    for x in range(15, 18):
        for z in range(z1 + 1, 5):
            d.set(x, GY, z, "polished_andesite")
    # sliding blast door parked east of the portal on its track
    for x in range(18, 22):
        d.set(x, GY, z1 - 1, "polished_blackstone")
    for x in range(14, 18):
        d.set(x, GY, z1 - 1, "polished_blackstone")
    for x in range(19, 22):
        for y in range(SW, SW + 3):
            d.set(x, y, z1 - 1, "iron_block" if y != SW + 1 else "heavy_core" if x == 20 else "iron_block")
    d.set(19, SW + 1, z1 - 2, "iron_trapdoor[facing=north,half=top,open=true,powered=false,waterlogged=false]")
    # sign and lamps on the front face
    d.sign(16, top, z1 - 1, "north", ["", "SHELTER 07", "CIVIL DEFENCE"], "birch", glow=True, color="yellow") \
        if False else None
    for x, txt in ((15, ["CIVIL"]), (16, ["SHELTER"]), (17, ["DEFENCE"])):
        d.sign(x, SW + 4, z1 - 1, "north", ["", txt[0], "07" if x == 16 else ""], "birch", glow=True, color="yellow")
    for x in (12, 20):
        d.set(x, SW + 2, z1 - 1, "end_rod[facing=north]")
    # grass berm over the back of the block
    for z in range(z1 + 3, z2 + 3):
        for x in range(x1 - 2, x2 + 3):
            if x1 <= x <= x2 and z <= z2:
                continue
            h = 3 - max(0, (x1 - x) if x < x1 else (x - x2) if x > x2 else 0) - max(0, z - z2)
            for y in range(SW, SW + max(0, h)):
                d.set(x, y, z, "dirt" if y < SW + h - 1 else "grass_block[snowy=false]")
    d.fill(x1, top + 1, z1 + 3, x2, top + 1, z2, "moss_carpet")
    d.fill(x1, top, z1 + 3, x2, top, z2, "moss_block")
    for x in range(x1, x2 + 1):
        d.set(x, top, z1 + 2, "smooth_stone_slab[type=bottom,waterlogged=false]")
    # bollards and planters along the approach
    for x in (10, 22):
        for z in (0, 4):
            d.set(x, SW, z, "andesite_wall")
    for z in (6, 9):
        d.set(9, SW, z, "potted_bamboo")
        d.set(23, SW, z, "potted_bamboo")
    if L >= 2:              # periscope / air intake mushroom heads on the lawn
        for (px, pz) in ((5, 20), (27, 26)):
            d.set(px, SW, pz, "andesite_wall")
            d.set(px, SW + 1, pz, "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    if L >= 3:              # solar field on frames
        for z in range(18, 30, 3):
            for x in range(17, 30):
                d.set(x, SW, z, "smooth_stone_slab[type=top,waterlogged=false]")
                d.set(x, SW + 1, z, "daylight_detector[inverted=false,power=0]")
                d.set(x, SW, z + 1, "smooth_stone_slab[type=bottom,waterlogged=false]") if False else None
    if L >= 4:              # guard booth and perimeter fence with a gate
        bx1, bz1 = 3, 2
        d.box(bx1, SW, bz1, bx1 + 4, SW + 2, bz1 + 3, "white_concrete")
        d.fill(bx1, SW + 3, bz1, bx1 + 4, SW + 3, bz1 + 3, "smooth_quartz_slab[type=bottom,waterlogged=false]")
        for x in range(bx1 + 1, bx1 + 4):
            d.set(x, SW + 1, bz1, "glass_pane")
            d.set(x, SW + 1, bz1 + 3, "glass_pane")
        d.door(bx1 + 4, SW, bz1 + 2, "east", "birch")
        d.chair(bx1 + 2, SW, bz1 + 1, "south", "birch", sit=False)
        d.set(bx1 + 1, SW, bz1 + 1, "smooth_quartz_slab[type=top,waterlogged=false]")
        d.set(bx1 + 2, SW + 2, bz1 + 2, "sea_lantern")
        for x in range(0, sx):
            if 9 <= x <= 23 or x in (sx // 2,):
                continue
            d.set(x, SW, sz - 1, "iron_bars")
        for z in range(6, sz):
            d.set(0, SW, z, "iron_bars")
            d.set(sx - 1, SW, z, "iron_bars") if z not in range(11, 16) else None
    if L >= 5:              # radio mast with a beacon light
        mx, mz = 6, 12
        d.set(mx, SW, mz, "polished_andesite")
        for y in range(SW + 1, SW + 10):
            d.set(mx, y, mz, "iron_bars" if y % 3 else "andesite_wall")
        d.set(mx, SW + 10, mz, "redstone_lamp[lit=true]")
        d.set(mx, SW + 11, mz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        for dx, dz in D4.values():
            d.set(mx + dx, SW, mz + dz, "andesite_wall")
    return d


# ---------------------------------------------------------------------------------------------------- Hearthwood
def hearthwood(rel, L):
    P = PLANS["Hearthwood"]
    sx, sy, sz = P["size"]
    d = Design("Hearthwood", rel, (sx, sy, sz), gy=GY, paving="grass_block[snowy=false]")
    bunker_common(d, "Hearthwood", L)
    M = MATS["Hearthwood"]
    # ---- the air shaft: garden well over the link corridor
    wx, wz = 13, 19
    for y in range(22, GY + 1):
        for dx in (-1, 0, 1, 2):
            for dz in (-1, 0, 1):
                if not (0 <= dx <= 1 and dz == 0):
                    put_wall(d, "Hearthwood", wx + dx, y, wz + dz, 18)
        d.set(wx, y, wz, AIR)
        d.set(wx + 1, y, wz, AIR)
    d.set(wx, 22, wz, "iron_bars")
    d.set(wx + 1, 22, wz, "iron_bars")
    for dx in (-1, 0, 1, 2):
        for dz in (-1, 0, 1):
            if not (0 <= dx <= 1 and dz == 0):
                d.set(wx + dx, SW, wz + dz, "mossy_cobblestone" if (dx + dz) % 2 else "cobblestone")
    for x in (wx - 1, wx + 2):
        d.set(x, SW + 1, wz, "oak_fence")
        d.set(x, SW + 2, wz, "oak_fence")
    for x in range(wx - 1, wx + 3):
        d.set(x, SW + 3, wz, "dark_oak_slab[type=bottom,waterlogged=false]")
        d.set(x, SW + 3, wz - 1, "deepslate_tile_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
        d.set(x, SW + 3, wz + 1, "deepslate_tile_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")
    d.set(wx, SW + 2, wz, "chain[axis=y,waterlogged=false]")
    d.set(wx, SW + 1, wz, "lantern[hanging=true,waterlogged=false]")
    d.set(wx + 1, SW, wz, "iron_bars")
    d.set(wx, SW, wz, "iron_bars")
    # ---- the ruined chapel around the stair head
    cx1, cx2, cz1, cz2 = 0, 11, 0, 11
    for z in range(cz1, cz2 + 1):
        for x in range(cx1, cx2 + 1):
            if x in (cx1, cx2) or z in (cz1, cz2):
                h = 5 - (H(x, 0, z) % 4) if not (z == cz1 and 4 <= x <= 7) else 6
                if z == cz2:
                    h = 2 + H(x, 1, z) % 3
                if x == cx2 and z > 6:
                    h = 1 + H(x, 2, z) % 2
                for y in range(SW, SW + h):
                    d.set(x, y, z, wall_block("Hearthwood", x, y, z, -1))
    d.fill(cx1 + 1, GY, cz1 + 1, cx2 - 1, GY, cz2 - 1, "stone_bricks")
    for z in range(cz1 + 1, cz2):
        for x in range(cx1 + 1, cx2):
            if H(x, 3, z) < 30:
                d.set(x, GY, z, "mossy_stone_bricks")
            if H(x, 4, z) < 10 and d.air(x, SW, z):
                d.set(x, GY, z, "grass_block[snowy=false]")
    # west gable (street side) with a broken pointed window and a doorway
    for x in (4, 7):
        for y in range(SW, SW + 7):
            d.set(x, y, cz1, "stone_bricks")
    for y in range(SW, SW + 2):
        d.set(5, y, cz1, AIR)
        d.set(6, y, cz1, AIR)
    d.set(5, SW + 2, cz1, st("stone_brick_stairs", "east", "top"))
    d.set(6, SW + 2, cz1, st("stone_brick_stairs", "west", "top"))
    for y in (SW + 4, SW + 5):
        d.set(5, y, cz1, "glass_pane" if y == SW + 4 else st("stone_brick_stairs", "east", "top"))
        d.set(6, y, cz1, "glass_pane" if y == SW + 4 else st("stone_brick_stairs", "west", "top"))
    d.set(5, SW + 6, cz1, "stone_bricks")
    d.set(6, SW + 6, cz1, "stone_bricks")
    for y in range(SW + 3, SW + 7):
        for x in (4, 5, 6, 7):
            if y == SW + 3:
                d.set(x, y, cz1, "stone_bricks")
    # pointed arch over the cellar steps
    x0, w, zf = P["ramp"]
    for y in range(SW, SW + 3):
        d.set(x0 - 1, y, zf, "chiseled_stone_bricks" if y == SW + 2 else "stone_bricks")
        d.set(x0 + w, y, zf, "chiseled_stone_bricks" if y == SW + 2 else "stone_bricks")
    d.set(x0, SW + 3, zf, st("stone_brick_stairs", "east", "top"))
    d.set(x0 + 1, SW + 3, zf, st("stone_brick_stairs", "west", "top"))
    d.set(x0 - 1, SW + 3, zf, "stone_bricks")
    d.set(x0 + w, SW + 3, zf, "stone_bricks")
    d.set(x0, SW + 4, zf, "stone_brick_slab[type=bottom,waterlogged=false]")
    d.set(x0 + 1, SW + 4, zf, "stone_brick_slab[type=bottom,waterlogged=false]")
    # low parapet round the stair well inside the ruin, with an old oak lid-door propped open
    for z in range(zf + 1, zf + 6):
        d.set(x0 + w, SW, z, "stone_brick_wall")
        if not d.air(x0 - 1, GY, z):
            d.set(x0 - 1, SW, z, "stone_brick_wall") if x0 - 1 > cx1 else None
    d.set(x0 + w, SW + 1, zf + 1, "lantern[hanging=false,waterlogged=false]")
    d.set(x0, SW, zf - 1, "dark_oak_trapdoor[facing=south,half=bottom,open=true,powered=false,waterlogged=false]")
    # ivy and nature on the ruin
    for x in range(cx1, cx2 + 1):
        for y in range(SW, SW + 6):
            if not d.air(x, y, cz1) and d.air(x, y, cz1 - 1) if cz1 > 0 else False:
                d.set(x, y, cz1 - 1, "vine[east=false,north=false,south=true,up=false,west=false]")
    for (x, z) in ((9, 3), (8, 8), (1 + 0, 9)):
        if d.air(x, SW, z) and x not in range(x0 - 1, x0 + w + 1):
            d.set(x, SW, z, "fern" if (x + z) % 2 else "sweet_berry_bush[age=1]")
    # ---- cottage garden: gravel path, flower beds, hedges, benches
    for z in range(cz2, sz):
        d.set(5, GY, z, "gravel")
        d.set(6, GY, z, "gravel")
    for x in range(6, 26):
        d.set(x, GY, 16, "gravel")
    for x in range(13, 27):
        for z in (0, 1):
            d.set(x, GY, z, "gravel" if z == 1 else "grass_block[snowy=false]")
    flowers = ["poppy", "dandelion", "azure_bluet", "oxeye_daisy", "cornflower", "allium", "rose_bush[half=lower]"]
    for x in range(13, 27):
        if x % 7 == 0:
            continue
        f = flowers[x % len(flowers)]
        if f.startswith("rose"):
            d.set(x, SW, 3, "rose_bush[half=lower]")
            d.set(x, SW + 1, 3, "rose_bush[half=upper]")
        else:
            d.set(x, SW, 3, f)
        d.set(x, GY, 3, "grass_block[snowy=false]")
    for x in range(12, 28):
        d.set(x, SW, 5, "oak_leaves[distance=7,persistent=true,waterlogged=false]") if x % 6 else None
    for z in range(6, sz - 1):
        d.set(sx - 1, SW, z, "oak_leaves[distance=7,persistent=true,waterlogged=false]")
        if z > 12:
            d.set(0, SW, z, "oak_leaves[distance=7,persistent=true,waterlogged=false]")
    for x in range(1, sx - 1):
        if x not in (5, 6):
            d.set(x, SW, sz - 1, "oak_leaves[distance=7,persistent=true,waterlogged=false]")
    # old yew tree
    tx, tz = 21, 10
    for y in range(SW, SW + 4):
        d.set(tx, y, tz, "dark_oak_log[axis=y]")
    for dy in range(3, 7):
        r = 2 if dy < 6 else 1
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if abs(dx) + abs(dz) <= r + 1 and d.air(tx + dx, SW + dy, tz + dz):
                    d.set(tx + dx, SW + dy, tz + dz, "spruce_leaves[distance=7,persistent=true,waterlogged=false]")
    d.chair(19, SW, 13, "south", "dark_oak", sit=False)
    d.chair(20, SW, 13, "south", "dark_oak", sit=False)
    if L >= 2:              # vegetable patch with water butt
        for x in range(17, 26):
            for z in range(19, 25):
                if x in (17, 25) or z in (19, 24):
                    d.set(x, SW, z, "oak_fence")
                elif z == 21:
                    d.set(x, GY, z, "water")
                else:
                    d.set(x, GY, z, "farmland[moisture=7]")
                    d.set(x, SW, z, ["carrots[age=5]", "potatoes[age=6]", "beetroots[age=2]"][x % 3])
        d.set(21, SW, 19, "oak_fence_gate[facing=north,in_wall=false,open=false,powered=false]")
        d.set(16, SW, 19, "barrel[facing=up,open=false]")
        d.set(16, SW + 1, 19, "oak_pressure_plate[powered=false]") if False else None
    if L >= 3:              # potting shed against the hedge (hides a second vent)
        sx1, sz1 = 20, 27
        d.box(sx1, SW, sz1, sx1 + 5, SW + 2, sz1 + 3, "oak_planks")
        for x in range(sx1, sx1 + 6):
            for z in range(sz1, sz1 + 4):
                if x in (sx1, sx1 + 5) and z in (sz1, sz1 + 3):
                    for y in range(SW, SW + 3):
                        d.set(x, y, z, "dark_oak_log[axis=y]")
        d.gable(sx1, sz1, sx1 + 5, sz1 + 3, SW + 3, "x", "deepslate_tile_stairs", "deepslate_tile_slab", "oak_planks")
        d.door(sx1 + 2, SW, sz1, "south", "dark_oak")
        d.set(sx1 + 4, SW + 1, sz1, "glass_pane")
        d.set(sx1 + 1, SW, sz1 + 2, "composter[level=4]")
        d.set(sx1 + 4, SW, sz1 + 2, "dark_oak_slab[type=top,waterlogged=false]")
        d.set(sx1 + 4, SW + 1, sz1 + 2, "potted_red_tulip")
    if L >= 4:              # pergola walk with roses
        for z in range(13, 26, 3):
            for x in (4, 7):
                d.set(x, SW, z, "dark_oak_fence")
                d.set(x, SW + 1, z, "dark_oak_fence")
            for x in range(4, 8):
                d.set(x, SW + 2, z, "dark_oak_slab[type=bottom,waterlogged=false]")
        for z in range(13, 26):
            d.set(4, SW + 2, z, "oak_leaves[distance=7,persistent=true,waterlogged=false]") if z % 3 else None
    if L >= 5:              # restored bell-cote on the ruin's gable
        for y in range(SW + 7, SW + 10):
            d.set(4, y, 0, "stone_bricks")
            d.set(7, y, 0, "stone_bricks")
        d.set(5, SW + 8, 0, "bell[attachment=double_wall,facing=east,powered=false]")
        for x in range(3, 9):
            d.set(x, SW + 10, 0, "deepslate_tile_slab[type=bottom,waterlogged=false]")
        d.set(5, SW + 10, 0, "deepslate_tiles")
        d.set(6, SW + 10, 0, "deepslate_tiles")
        d.set(5, SW + 11, 0, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    return d


# ---------------------------------------------------------------------------------------------------- Cascadia
def cascadia(rel, L):
    P = PLANS["Cascadia"]
    sx, sy, sz = P["size"]
    d = Design("Cascadia", rel, (sx, sy, sz), gy=GY, paving="grass_block[snowy=false]")
    bunker_common(d, "Cascadia", L)
    M = MATS["Cascadia"]
    x0, w, zf = P["ramp"]
    # ---- the rock knoll (heightmap), cliff face on the north side
    knoll = {}
    for x in range(1, sx - 1):
        for z in range(5, sz - 1):
            fx = (x - 16) / 15.0
            fz = (z - 17) / 12.5
            h = 9.0 * (1 - fx * fx - fz * fz) + (H(x, 0, z) % 3) - 1
            if z < 9:
                h = min(h, 9 - 0.5 * (9 - z) if z >= 6 else 0)
            h = int(h)
            if h > 0:
                knoll[(x, z)] = h
    for (x, z), h in knoll.items():
        for y in range(SW, SW + h):
            top = y == SW + h - 1
            hh = H(x, y, z, 5)
            if top and z > 6:
                b = "grass_block[snowy=false]" if hh < 60 else "moss_block" if hh < 80 else "coarse_dirt"
            else:
                b = wall_block("Cascadia", x, y, z, -1)
            d.set(x, y, z, b)
    # adit: timbered tunnel into the cliff at surface level, then the incline
    adz1 = 3
    for z in range(adz1, zf):
        for x in range(x0 - 1, x0 + w + 1):
            for y in range(SW, SW + 4):
                inner = x0 <= x < x0 + w and y < SW + 3
                if inner:
                    d.set(x, y, z, AIR)
                elif (x, z) in knoll or z >= 5:
                    d.set(x, y, z, wall_block("Cascadia", x, y, z, -1))
        for x in range(x0, x0 + w):
            d.set(x, GY, z, "gravel")
    for z in range(zf, zf + 6):                        # keep the incline's head clear of rock
        i = z - zf + 1
        for x in range(x0, x0 + w):
            for y in range(SW - i, SW - i + 4):
                if y >= SW:
                    d.set(x, y, z, AIR)
        for x in (x0 - 1, x0 + w):
            for y in range(SW, SW + 4):
                if not d.air(x, y, z) or (x, z) in knoll:
                    d.set(x, y, z, wall_block("Cascadia", x, y, z, -1))
    for z in range(zf, zf + 6):
        i = z - zf + 1
        if SW - i + 4 >= SW:
            for x in range(x0, x0 + w):
                yy = SW - i + 4
                if yy < SW + 4:
                    d.set(x, yy, z, "spruce_planks")
    for z in range(adz1, zf, 2):                       # timber sets
        for y in range(SW, SW + 3):
            d.set(x0 - 1, y, z, "spruce_log[axis=y]")
            d.set(x0 + w, y, z, "spruce_log[axis=y]")
        for x in range(x0 - 1, x0 + w + 1):
            d.set(x, SW + 3, z, "spruce_log[axis=x]")
    # portal: heavy timber set proud of the cliff, name board, lamps
    pz = adz1 - 1
    for y in range(SW, SW + 4):
        d.set(x0 - 1, y, pz, "spruce_log[axis=y]")
        d.set(x0 + w, y, pz, "spruce_log[axis=y]")
    for x in range(x0 - 2, x0 + w + 2):
        d.set(x, SW + 4, pz, "spruce_log[axis=x]")
        d.set(x, SW + 4, pz + 1, "spruce_log[axis=x]")
        d.set(x, SW + 5, pz, "spruce_slab[type=bottom,waterlogged=false]")
    for x in range(x0, x0 + w):
        d.set(x, SW + 3, pz, "spruce_slab[type=top,waterlogged=false]")
    d.sign(x0 + 1, SW + 4, pz - 1, "north", ["RIDGE", "REFUGE", "~ No. 3 Adit ~"], "spruce")
    d.set(x0 - 2, SW + 3, pz, "lantern[hanging=true,waterlogged=false]") if False else None
    d.set(x0 - 1, SW + 3, pz - 1, "lantern[hanging=true,waterlogged=false]")
    d.set(x0 + w, SW + 3, pz - 1, "lantern[hanging=true,waterlogged=false]")
    # rails from the adit out into the yard, ore cart (barrel) at the end
    for z in range(0, zf):
        d.set(x0 + 1, SW, z, "rail[shape=north_south,waterlogged=false]")
        d.set(x0 + 1, GY, z, "gravel")
    d.fill(x0 - 2, GY, 0, x0 + w + 1, GY, 1, "coarse_dirt")
    # rock face detail: moss, a spruce or two on the knoll
    for (tx, tz) in ((9, 13), (23, 15), (14, 22), (25, 22)):
        h = knoll.get((tx, tz))
        if not h:
            continue
        base = SW + h
        for y in range(base, base + 5):
            d.set(tx, y, tz, "spruce_log[axis=y]")
        for dy in range(2, 7):
            r = 2 if dy < 4 else 1 if dy < 6 else 0
            for dx in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    if (dx, dz) != (0, 0) or dy >= 5:
                        if abs(dx) + abs(dz) <= r + (1 if r == 2 else 0) and d.air(tx + dx, base + dy, tz + dz):
                            d.set(tx + dx, base + dy, tz + dz,
                                  "spruce_leaves[distance=7,persistent=true,waterlogged=false]")
    # ---- ventilation stack from the boiler room up through the knoll
    vx, vz = P["vent"]
    vtop = SW + knoll.get((vx, vz), 0) + 2
    for y in range(18, vtop):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if (dx, dz) != (0, 0) and y <= GY:
                    put_wall(d, "Cascadia", vx + dx, y, vz + dz, 13)
                elif (dx, dz) != (0, 0) and y > GY and not d.air(vx + dx, y, vz + dz):
                    pass
        d.set(vx, y, vz, AIR)
    d.set(vx, 18, vz, "iron_bars")
    for y in range(SW + knoll.get((vx, vz), 0) - 1, vtop):
        for dx, dz in D4.values():
            d.set(vx + dx, y, vz + dz, "cobblestone" if y < vtop - 1 else "mossy_cobblestone")
    d.set(vx, vtop, vz, "iron_bars")
    for dx, dz in D4.values():
        d.set(vx + dx, vtop, vz + dz, "cobblestone_slab[type=bottom,waterlogged=false]")
    # ---- blacksmith's lean-to at the foot of the rock face (the workshop)
    bx1, bx2, bz1, bz2 = 20, 30, 0, 4
    d.fill(bx1, GY, bz1, bx2, GY, bz2, "spruce_planks")
    for x in range(bx1, bx2 + 1):
        for y in range(SW, SW + 4):
            d.set(x, y, bz2 + 1, wall_block("Cascadia", x, y, bz2 + 1, -1))
    for x in (bx1, bx2, (bx1 + bx2) // 2):
        for y in range(SW, SW + 3):
            d.set(x, y, bz1, "spruce_log[axis=y]")
    for z in range(bz1 - 0, bz2 + 1):
        for y in range(SW, SW + 3):
            d.set(bx2, y, z, "spruce_log[axis=y]" if z in (bz1, bz2) else "spruce_planks")
    for x in range(bx1 - 1, bx2 + 2):
        for z in range(bz1, bz2 + 2):
            yy = SW + 3 + (z - bz1) // 2
            if d.bp.inside(x, yy, z):
                d.set(x, yy, z, "spruce_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]"
                      if z % 2 == 0 else "spruce_slab[type=top,waterlogged=false]")
    R = room(bx1 + 1, bz1 + 1, bx2 - 1, bz2, SW, SW + 2, keep=set())
    # front is open: keep its row free so the work blocks stand along the back and the east end
    R.keep = {(x, bz1 + 1) for x in range(bx1 + 1, bx2)}
    f_workshop(d, R, M, L, "Cascadia", outdoor=True)
    d.set((bx1 + bx2) // 2 - 2, SW + 2, bz1 + 1, "lantern[hanging=true,waterlogged=false]")
    d.set((bx1 + bx2) // 2 + 2, SW + 2, bz1 + 1, "lantern[hanging=true,waterlogged=false]")
    d.set(bx1 - 1, SW, 1, "water_cauldron[level=3]")   # quench tub
    d.sign((bx1 + bx2) // 2, SW + 2, bz1 - 1, "north", ["SMITHY", "& TOOL SHOP"], "spruce")
    # yard: split-log fence, woodpile, crates
    for x in range(1, 12):
        d.set(x, SW, 0, "spruce_fence")
    for x in range(3, 9):
        d.set(x, SW, 3, "spruce_log[axis=x]")
        if x % 2:
            d.set(x, SW + 1, 3, "spruce_log[axis=x]")
    if L >= 2:
        d.set(x0 + 1, SW, 1, "barrel[facing=up,open=false]") if False else None
        d.set(12, SW, 2, "hay_block[axis=y]")
        d.set(12, SW + 1, 2, "barrel[facing=up,open=false]") if False else None
    if L >= 3:              # ore chute and lamp posts
        for (lx, lz) in ((x0 - 3, 1), (x0 + w + 2, 1)):
            for y in range(SW, SW + 3):
                d.set(lx, y, lz, "spruce_fence")
            d.set(lx, SW + 3, lz, "lantern[hanging=false,waterlogged=false]")
        for y in range(SW + 1, SW + 4):
            d.set(9, y, 6, "spruce_planks") if (9, 6) in knoll else None
    if L >= 5:              # lookout platform on the knoll top
        top = max(knoll.values())
        tx, tz = 17, 17
        base = SW + knoll.get((tx, tz), top)
        for (px, pz) in ((tx - 1, tz - 1), (tx + 1, tz - 1), (tx - 1, tz + 1), (tx + 1, tz + 1)):
            for y in range(SW + knoll.get((px, pz), 0), base + 4):
                d.set(px, y, pz, "spruce_log[axis=y]")
        d.fill(tx - 1, base + 4, tz - 1, tx + 1, base + 4, tz + 1, "spruce_planks")
        for (px, pz) in ((tx - 2, tz), (tx + 2, tz), (tx, tz - 2), (tx, tz + 2)):
            d.set(px, base + 5, pz, "spruce_fence") if False else None
        for x in range(tx - 1, tx + 2):
            for z in (tz - 1, tz + 1):
                d.set(x, base + 5, z, "spruce_fence")
        d.set(tx - 1, base + 5, tz, "spruce_fence")
        d.set(tx + 1, base + 5, tz, "spruce_fence")
        d.set(tx, base + 5, tz, "lantern[hanging=false,waterlogged=false]")
    return d


@design("bunker")
def bunker(pack, rel, L):
    return {"Neoterra": neoterra, "Hearthwood": hearthwood, "Cascadia": cascadia}[pack](rel, L)
