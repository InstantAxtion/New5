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
from designs._bunker_plans import ROOMPLANS, CHILD_PLANS, CORR_LIGHTS, FLOORS

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
    wells=[(30, 28, "A", "B", 2, +1), (30, 46, "B", "C", 4, +1)],          # lane-1 x, z0, upper deck, lower deck, minL, lane-2 side
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
        ("gym", "A", 30, 36, 40, 40, 3),
        ("office", "A", 42, 36, 52, 40, 4),
        ("chapel", "A", 2, 46, 12, 52, 3),
        ("bunks", "A", 14, 46, 24, 52, 5),
        ("store", "A", 30, 46, 40, 52, 4),
        ("canteen", "A", 42, 46, 52, 52, 4),
        ("corr", "A", 13, 11, 21, 13, 3),
        ("suitroom", "A", 2, 1, 11, 13, 3),
        ("gallery", "A", 34, 11, 52, 14, 4),
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
        ("armory", "B", 2, 28, 24, 34, 4),
        ("cistern", "B", 34, 28, 52, 34, 5),
        ("turbine", "B", 2, 36, 24, 44, 4),
        ("hydro", "B", 30, 36, 40, 44, 4),
        ("bunks", "B", 42, 36, 52, 44, 4),
        ("workshop", "B", 2, 46, 24, 52, 5),
        ("mess", "B", 33, 46, 52, 52, 5),
        # ---- deck C (plant deck)
        ("corr", "C", 2, 42, 52, 44, 4),
        ("reactor", "C", 2, 34, 24, 40, 4),
        ("power", "C", 26, 34, 52, 40, 5),
        ("server", "C", 2, 46, 27, 52, 5),
        ("armory", "C", 34, 46, 52, 52, 5),
        ("corr", "C", 26, 2, 28, 32, 5),             # L5: the deep north wing off a spine through the switch hall
        ("dwellC", "C", 2, 2, 24, 14, 5),
        ("wardC", "C", 2, 16, 24, 32, 5),
        ("vaultC", "C", 30, 2, 52, 14, 5),
        ("commandC", "C", 30, 16, 52, 32, 5),
    ],
    doors=[  # every door / opening, by hand: (x, z, deck, from level, kind)
        (22, 10, "A", 1, "vault"), (31, 10, "A", 1, "door"), (7, 23, "A", 1, "door"), (23, 15, "A", 1, "door"),
        (31, 15, "A", 1, "door"), (7, 27, "A", 1, "door"), (25, 30, "A", 1, "door"), (36, 27, "A", 1, "door"),
        (29, 28, "A", 2, "open"), (47, 23, "A", 3, "door"), (47, 27, "A", 3, "door"), (7, 41, "A", 3, "door"),
        (25, 38, "A", 3, "door"), (29, 38, "A", 3, "door"), (7, 45, "A", 3, "door"), (47, 41, "A", 4, "door"),
        (29, 49, "A", 4, "door"), (47, 45, "A", 4, "door"), (45, 5, "A", 4, "door"), (25, 49, "A", 5, "door"),
        (35, 23, "B", 2, "door"), (47, 23, "B", 2, "door"), (25, 8, "B", 2, "vault"), (31, 27, "B", 2, "open"),
        (7, 23, "B", 3, "door"), (19, 23, "B", 3, "door"), (29, 8, "B", 3, "door"), (13, 27, "B", 4, "door"),
        (25, 40, "B", 4, "door"), (29, 40, "B", 4, "door"), (41, 40, "B", 4, "door"), (7, 15, "B", 4, "door"),
        (47, 15, "B", 4, "door"), (12, 12, "A", 3, "door"), (33, 12, "A", 4, "door"), (43, 27, "B", 5, "door"), (25, 49, "B", 5, "door"), (36, 45, "B", 5, "door"),
        (29, 46, "B", 4, "open"),
        (13, 41, "C", 4, "door"), (39, 41, "C", 5, "door"), (27, 33, "C", 5, "open"), (25, 8, "C", 5, "door"),
        (29, 8, "C", 5, "door"), (25, 24, "C", 5, "door"), (29, 24, "C", 5, "door"), (14, 45, "C", 5, "door"), (43, 45, "C", 5, "door"),
        (31, 45, "C", 4, "open")],
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
    P["spaces_base"] = list(base["spaces"])
    P["mirror"], P["dz"] = mirror, dz
    return P


PLANS = {
    "Neoterra": dict(size=(55, 62, 55), **_transform(BASE, 55)),
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


def flush_ok(d, x, y, z):
    """A flush ceiling light only where the ceiling is ours and nothing walks on top of it."""
    if not d.bp.inside(x, y, z):
        return False
    here = d.get(x, y, z)
    if here == AIR or "substitution" in here or not d.bp.inside(x, y + 1, z):
        return False
    above = d.get(x, y + 1, z)
    return above != AIR and "blocksubstitution" not in above


# ---------------------------------------------------------------------------------------------------- furnishers
# ---------------------------------------------------------------------------------------------------- children


CORR_KINDS = ("corr", "hall")


def active(pack, L):
    return [s for s in PLANS[pack]["spaces"] if s[6] <= L]


def level_doors(pack, L):
    """The plan's hand-listed doors that exist at level L."""
    return [(x, z, dk, kind) for (x, z, dk, ml, kind) in PLANS[pack]["doors"] if ml <= L]


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
    d.hut(hx - x1, 1, hz - z1, "north")
    mir = PLANS[pack]["mirror"]
    stamp(d, CHILD_PLANS[pack][kind], lambda i, j: ((W - 1 - i) if mir else i, j), (0, 0, W - 1, D - 1), 1,
          cy - 1, cy, L, sit=kind != "clinic", keep=lk | {(hx - x1, hz - z1)}, mirror=mir)
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


INTO = {"north": "south", "south": "north", "west": "east", "east": "west"}


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


# ---------------------------------------------------------------------------------------------------- surface buildings
def building(d, pal, x1, z1, x2, z2, nfl, door, L, style, roof="flat", chimney=None):
    """Shell of a surface building (structure only): nfl storeys of 4 (3 air), walls with the window openings of its
    style, the door, a straight stair in alternating corners (flight k at x1+1 / x2-1, z1+1..z1+4), roof, chimney.
    Furniture, railings, lights and exterior dressing are placed by hand per building (stamp_floor / place)."""
    dx_, dz_, dfac = door
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
                n = (x2 - x1) if z in (z1, z2) else (z2 - z1)
                if 2 <= along <= n - 2 and not corner and not post and along % 2 == 1:
                    if (x, z) == (dx_, dz_) or abs((x - dx_) + (z - dz_)) <= 1 and (x == dx_ or z == dz_):
                        continue
                    for y in ((yf + 1, yf + 2) if style == "modern" or k == 0 else (yf + 2,)):
                        d.set(x, y, z, pal["glass"])
    Y = GY + 4 * nfl
    d.door(dx_, SW, dz_, dfac, pal["door"])
    for k in range(nfl - 1):
        yf = GY + 4 * k
        sx = x1 + 1 if k % 2 == 0 else x2 - 1
        for i in range(4):
            z = z1 + 1 + i
            for y in range(yf + 1, yf + 1 + i):
                d.set(sx, y, z, pal["floor"])
            d.set(sx, yf + 1 + i, z, st(pal["stairs"], "north"))
            for y in range(yf + 2 + i, yf + 5 + i):
                d.set(sx, y, z, AIR)
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
            d.set(cx, ridge + 3, cz, "brick_slab[type=bottom,waterlogged=false]" if "brick" in pal.get("chimney", "bricks")
                  else "cobblestone_slab[type=bottom,waterlogged=false]")


# ---------------------------------------------------------------------------------------------------- hand plans
# Every room is furnished from a plan drawn by hand for that room of that pack (designs below). A plan is a list of
# rows (north -> south) of characters (west -> east), one character per floor cell, drawn in the BASE orientation;
# Hearthwood's mirrored complex stamps its own plans mirrored. Nothing decides positions by itself: each character is
# one piece at that cell. Wall-standing pieces turn to face away from the wall they stand against.
#   .  nothing            *  ceiling light above    =  rug border         -  rug centre        |  railing (fence)
#   ^ v < >  chair, backrest to the north / south / west / east          N S E W  bed, head to that side
#   t  table (post)       T  table (slab)          k  counter + candle    K  counter + lantern  d  display case
#   c  crate (barrel)     C  two crates            a  sacks               p  shelf + pot        P  potted plant
#   f  flowering azalea   b  bookcase (2)          q  chiseled case (2)   L  locker             u  wash basin
#   r  medicine shelf     m  machine               g  water tank          o  console            y  radio set
#   x  weapon rack        X  archery target        H  hay bale            h  punch bag          z  planter
#   i  lab bench          B  blackboard            l  loom (decor)        n  anvil (decor)      s  grindstone (decor)
#   required work blocks (counted):  J jukebox  M cartography  F furnace  Q blast furnace  Y smoker  G grindstone
#   A anvil  I smithing  U crafting  O stonecutter  V fletching  D loom  Z enchanting  e lectern  w water cauldron
#   j brewing stand (on a shelf)  % composter  & ender chest  0 barrel  $ barrel stack (3)  R rack
#   [ bookcase column (3)  ] chiseled column (3)  { bookcase (2)  ! work spot (tag only)
# Digits / other characters are level gates defined per plan: gate[c] = (from level, char if reached, char before).
MIRROR_CH = {"<": ">", ">": "<", "E": "W", "W": "E"}
POTS2 = ["decorated_pot[cracked=false,facing=north,waterlogged=false]", "potted_fern", "potted_azure_bluet",
         "candle[candles=3,lit=false,waterlogged=false]", "potted_bamboo", "potted_red_tulip"]


def piece(d, ch, x, y, z, fac, M, pack, L, top, ceil_y, sit, k):
    """Draw ONE piece `ch` at (x, y, z); fac = side it faces."""
    wood = M["wood"]
    S = d.set

    def counter():
        return M["counter"] if pack != "Neoterra" else "smooth_stone"
    if ch in ".# ":
        return
    if ch == "*":
        if pack == "Neoterra" and flush_ok(d, x, ceil_y, z):
            S(x, ceil_y, z, "sea_lantern" if L >= 4 else "glowstone")
        elif top - y >= 3 and pack != "Neoterra":
            S(x, top, z, "chain[axis=y,waterlogged=false]")
            S(x, top - 1, z, "lantern[hanging=true,waterlogged=false]")
        else:
            S(x, top, z, "lantern[hanging=true,waterlogged=false]")
        return
    rugs = {"Neoterra": ("light_gray_carpet", "cyan_carpet"), "Hearthwood": ("red_carpet", "brown_carpet"),
            "Cascadia": ("brown_carpet", "green_carpet")}[pack]
    if ch in "=-":
        S(x, y, z, rugs[0 if ch == "=" else 1])
    elif ch == "|":
        S(x, y, z, f"{wood}_fence" if pack != "Neoterra" else "birch_fence")
    elif ch in "^v<>":
        d.chair(x, y, z, {"^": "north", "v": "south", "<": "west", ">": "east"}[ch], wood, sit=sit)
    elif ch in "NSEW":
        d.bed(x, y, z, {"N": "north", "S": "south", "E": "east", "W": "west"}[ch], M["bed"])
    elif ch == "t":
        d.table(x, y, z, wood, "post")
    elif ch == "T":
        d.table(x, y, z, wood, "slab", M["slab"])
    elif ch == "k":
        S(x, y, z, counter())
        S(x, y + 1, z, "candle[candles=2,lit=false,waterlogged=false]")
    elif ch == "K":
        S(x, y, z, counter())
        S(x, y + 1, z, "lantern[hanging=false,waterlogged=false]")
    elif ch == "d":
        S(x, y, z, counter())
        S(x, y + 1, z, POTS2[k % len(POTS2)])
    elif ch == "c":
        S(x, y, z, f"barrel[facing={fac},open=false]")
    elif ch == "C":
        S(x, y, z, f"barrel[facing={fac},open=false]")
        S(x, y + 1, z, "barrel[facing=up,open=false]")
    elif ch == "a":
        S(x, y, z, {"Neoterra": "light_gray_wool", "Hearthwood": "white_wool", "Cascadia": "brown_wool"}[pack])
        S(x, y + 1, z, {"Neoterra": "light_gray_carpet", "Hearthwood": "white_carpet", "Cascadia": "brown_carpet"}[pack])
    elif ch == "p":
        S(x, y, z, slab(M["slab"]))
        S(x, y + 1, z, POTS2[k % len(POTS2)])
    elif ch == "P":
        S(x, y, z, M["plant"])
    elif ch == "f":
        S(x, y, z, "flowering_azalea")
    elif ch == "b":
        S(x, y, z, "bookshelf")
        S(x, y + 1, z, "bookshelf")
    elif ch == "q":
        S(x, y, z, chiseled(fac, k))
        S(x, y + 1, z, chiseled(fac, k + 3))
    elif ch == "L":
        mat = {"Neoterra": "light_gray_concrete", "Hearthwood": "dark_oak_planks", "Cascadia": "spruce_planks"}[pack]
        S(x, y, z, mat)
        S(x, y + 1, z, f"{'iron' if pack == 'Neoterra' else wood}_trapdoor[facing={fac},half=bottom,open=true,"
                       f"powered=false,waterlogged=false]")
    elif ch == "u":
        S(x, y, z, "water_cauldron[level=3]")
    elif ch == "r":
        S(x, y, z, slab(M["slab"]))
        S(x, y + 1, z, "potted_white_tulip" if k % 2 else "candle[candles=1,lit=false,waterlogged=false]")
    elif ch == "m":
        if pack == "Neoterra":
            S(x, y, z, "cut_copper" if L >= 4 else "iron_block" if False else "light_gray_concrete")
            S(x, y + 1, z, "lightning_rod[facing=up,powered=false,waterlogged=false]" if L >= 4 else "stone_button"
              "[face=floor,facing=north,powered=false]")
        elif pack == "Hearthwood":
            S(x, y, z, "bricks")
            S(x, y + 1, z, "cauldron")
        else:
            S(x, y, z, "cobblestone")
            S(x, y + 1, z, "iron_bars")
        if top - y >= 3:
            S(x, y + 2, z, "chain[axis=y,waterlogged=false]")
    elif ch == "g":
        S(x, y, z, "light_blue_stained_glass")
        S(x, y + 1, z, "light_blue_stained_glass")
    elif ch == "o":
        if pack == "Neoterra":
            S(x, y, z, "polished_andesite")
            S(x, y + 1, z, "black_stained_glass_pane" if False else "daylight_detector[inverted=false,power=0]")
        elif pack == "Hearthwood":
            S(x, y, z, "dark_oak_planks")
            S(x, y + 1, z, "candle[candles=1,lit=false,waterlogged=false]")
        else:
            S(x, y, z, "spruce_planks")
            S(x, y + 1, z, "lantern[hanging=false,waterlogged=false]")
    elif ch == "y":
        S(x, y, z, "note_block[instrument=harp,note=0,powered=false]")
        S(x, y + 1, z, "jukebox[has_record=false]")
    elif ch == "x":
        S(x, y, z, f"{wood}_fence")
        S(x, y + 1, z, f"{wood}_trapdoor[facing={fac},half=top,open=true,powered=false,waterlogged=false]")
    elif ch == "X":
        S(x, y, z, "hay_block[axis=y]")
        S(x, y + 1, z, "target[power=0]")
    elif ch == "H":
        S(x, y, z, "hay_block[axis=y]")
    elif ch == "h":
        S(x, y + 1, z, "hay_block[axis=y]")
        for yy in range(y + 2, top + 1):
            S(x, yy, z, "chain[axis=y,waterlogged=false]")
    elif ch == "z":
        S(x, y, z, "moss_block")
        S(x, y + 1, z, "flowering_azalea" if k % 2 else "azalea")
    elif ch == "i":
        S(x, y, z, counter())
        S(x, y + 1, z, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
    elif ch == "B":
        S(x, y, z, slab(M["slab"]))
        b = "black_concrete" if pack == "Neoterra" else "black_terracotta" if pack == "Hearthwood" else "dark_oak_planks"
        S(x, y + 1, z, b)
        if top >= y + 2:
            S(x, y + 2, z, b)
    elif ch == "l":
        S(x, y, z, f"loom[facing={fac}]")
    elif ch == "n":
        S(x, y, z, f"anvil[facing={CW[fac]}]")
    elif ch == "s":
        S(x, y, z, f"grindstone[face=floor,facing={fac}]")
    # ---- counted work blocks
    elif ch in "JMFQYGAIUOVDZew%&0":
        name = {"J": "jukebox", "M": "cartography_table", "F": "furnace", "Q": "blast_furnace", "Y": "smoker",
                "G": "grindstone", "A": "anvil", "I": "smithing_table", "U": "crafting_table", "O": "stonecutter",
                "V": "fletching_table", "D": "loom", "Z": "enchanting_table", "e": "lectern",
                "w": "water_cauldron[level=3]", "%": "composter", "&": "ender_chest", "0": "barrel"}[ch]
        d.item(x, y, z, name, CW[fac] if ch in "AG" else ("up" if ch == "0" else fac))
        if ch in "FQY" and top >= y + 2 and pack != "Neoterra":
            S(x, y + 2, z, "bricks" if pack == "Hearthwood" else "cobblestone")
    elif ch == "j":
        S(x, y, z, slab(M["slab"]))
        d.item(x, y + 1, z, "brewing_stand")
    elif ch == "$":
        for h in range(3):
            d.item(x, y + h, z, "barrel", "up" if h == 2 else fac)
    elif ch == "R":
        d.rack(x, y, z, fac)
    elif ch == "[":
        d.bookshelf(x, y, z, 3)
    elif ch == "]":
        for h in range(3):
            d.item(x, y + h, z, chiseled(fac, k + h))
    elif ch == "{":
        d.bookshelf(x, y, z, 2)
    elif ch == "!":
        d.spot(x, y, z, "work")
    elif ch == ",":                                   # crop on farmland
        S(x, y - 1, z, "farmland[moisture=7]")
        S(x, y, z, ["wheat[age=7]", "carrots[age=7]", "potatoes[age=7]", "beetroots[age=3]"][(x + 2 * z) % 4])
    elif ch == "~":                                   # irrigation channel with a grow light over it
        S(x, y - 1, z, "water[level=0]")
        S(x, top, z, "glowstone" if L < 4 else {"Neoterra": "sea_lantern", "Hearthwood": "glowstone",
                                                "Cascadia": "ochre_froglight[axis=y]"}[pack])
    elif ch == ";":                                   # path
        S(x, y - 1, z, {"Neoterra": "polished_andesite", "Hearthwood": "gravel", "Cascadia": "coarse_dirt"}[pack])
    else:
        raise RuntimeError(f"unknown plan character {ch!r}")


def edge_facing(x, z, x1, z1, x2, z2, default="south"):
    if z == z1:
        return "south"
    if z == z2:
        return "north"
    if x == x1:
        return "east"
    if x == x2:
        return "west"
    return default


def stamp(d, plan, cells, rect, y, top, ceil_y, L, sit=False, keep=(), mirror=False):
    """Stamp a hand-drawn plan. cells(i, j) -> world (x, z) of plan column i, row j; rect = world interior box."""
    M, pack = MATS[d.pack], d.pack
    rows = plan["rows"] if isinstance(plan, dict) else plan
    gates = plan.get("gates", {}) if isinstance(plan, dict) else {}
    x1, z1, x2, z2 = rect
    W = abs(x2 - x1) + 1
    D = z2 - z1 + 1
    if len(rows) != D or any(len(r) != W for r in rows):
        raise RuntimeError(f"plan size {len(rows[0])}x{len(rows)} != room {W}x{D}: {rows[0]!r}")
    k = 0
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in gates:
                lv, a, b = gates[ch]
                ch = a if L >= lv else b
            if mirror:
                ch = MIRROR_CH.get(ch, ch)
            x, z = cells(i, j)
            if ch not in ".# *=-!" and (x, z) in keep:
                raise RuntimeError(f"plan puts {ch!r} on a door cell {(x, z)}")
            piece(d, ch, x, y, z, edge_facing(x, z, x1, z1, x2, z2), M, pack, L, top, ceil_y, sit, k)
            k += 1
    # hand-placed pendant / ceiling lights over tables and rugs (plan cells, drawn in the plan's orientation)
    for (i, j) in (plan.get("lights", ()) if isinstance(plan, dict) else ()):
        x, z = cells(i, j)
        piece(d, "*", x, y, z, "north", M, pack, L, top, ceil_y, sit, 0)


def stamp_room(d, pack, sp_base, sp_world, plan, L, sit=False):
    """Stamp a plan drawn in base orientation into a room of this pack's complex."""
    P = PLANS[pack]
    _, deck, bx1, bz1, bx2, bz2, _ = sp_base
    _, _, x1, z1, x2, z2, _ = sp_world
    fy, top = LV[deck]
    mir = P["mirror"]

    def cells(i, j):
        return ((54 - (bx1 + i)) if mir else bx1 + i), bz1 + j + P["dz"]
    keep = keep_for(pack, L, deck, x1, z1, x2, z2)
    stamp(d, plan, cells, (x1, z1, x2, z2), fy + 1, top, top + 1, L, sit, keep, mir)


def stamp_floor(d, x1, z1, plan, yf, L, sit=False):
    """Stamp a surface-building storey plan (world orientation) whose NW interior corner is (x1, z1)."""
    rows = plan["rows"] if isinstance(plan, dict) else plan
    W, D = len(rows[0]), len(rows)
    stamp(d, plan, lambda i, j: (x1 + i, z1 + j), (x1, z1, x1 + W - 1, z1 + D - 1), yf + 1, yf + 3, yf + 4, L, sit)


def place(d, items):
    """Hand-listed exterior pieces: (x, y, z, block)."""
    for (x, y, z, b) in items:
        d.set(x, y, z, b)


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
    # corridor lights (hand-listed)
    for (dk, bx, bz, ml) in CORR_LIGHTS[pack]:
        if ml <= L:
            x, z = ((54 - bx) if P["mirror"] else bx), bz + P["dz"]
            fy, top = LV[dk]
            piece(d, "*", x, fy + 1, z, "north", M, pack, L, top, top + 1, False, 0)
    if L >= 4:      # deck C plant corridor: a cable tray (chain run) under the ceiling along its north side
        fy, top = LV["C"]
        for bx in range(2, 53):
            x, z = ((54 - bx) if P["mirror"] else bx), 42 + P["dz"]
            d.set(x, top, z, "chain[axis=x,waterlogged=false]")
            if pack == "Cascadia":     # and the mine tramway along its middle
                d.set(x, fy + 1, z + 1, "rail[shape=east_west,waterlogged=false]")
    # rooms: each from its own hand-drawn plan
    for sp_w, sp_b in zip(P["spaces"], P["spaces_base"]):
        if sp_w[0] in CHILD_KINDS or sp_w[0] in CORR_KINDS or sp_w[6] > L:
            continue
        plan = ROOMPLANS[pack][(sp_b[1], sp_b[2], sp_b[3])]
        stamp_room(d, pack, sp_b, sp_w, plan, L, sit=sp_w[0] == "common")
    hx, hy, hz = P["hut"]
    d.hut(hx, hy, hz, "north")
    return spaces


def furnish(d, name, x1, z1, L):
    """Stamp each storey of a surface building from its hand-drawn plans (FLOORS)."""
    for k, rows in enumerate(FLOORS[d.pack][name]):
        stamp_floor(d, x1 + 1, z1 + 1, rows, GY + 4 * k, L)


def porch(d, x, z, out, slab_block, lamp="lantern[hanging=true,waterlogged=false]"):
    """One door canopy: a 3-wide slab hood over the door at (x, z) (opening to `out`) with two hanging lamps."""
    ox, oz = D4[out]
    sx, sz = (1, 0) if ox == 0 else (0, 1)
    for k in (-1, 0, 1):
        d.set(x + ox + sx * k, SW + 3, z + oz + sz * k, slab_block)
    for k in (-1, 1):
        d.set(x + ox + sx * k, SW + 2, z + oz + sz * k, lamp)


def window_box(d, x, y, z, out, wood, flower):
    """One flower box under the window at (x, y, z) of an outer wall facing `out`."""
    ox, oz = D4[out]
    d.set(x + ox, y - 2, z + oz, f"{wood}_trapdoor[facing={out},half=top,open=false,powered=false,waterlogged=false]")
    d.set(x + ox, y - 1, z + oz, flower)


def shutters(d, x, y, z, out, wood):
    """Pair of open shutters either side of the window at (x, y, z) on a wall facing `out`."""
    ox, oz = D4[out]
    sx, sz = (1, 0) if ox == 0 else (0, 1)
    for sgn, f in ((1, next(k for k, v in D4.items() if v == (sx, sz))), (-1, next(k for k, v in D4.items()
                                                                                  if v == (-sx, -sz)))):
        d.set(x + ox + sx * sgn, y, z + oz + sz * sgn,
              f"{wood}_trapdoor[facing={f},half=top,open=true,powered=false,waterlogged=false]")


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
    d = Design("Neoterra", rel, (sx, sy, sz), gy=GY, paving="grass_block")
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
                d.set(x, y, z, "dirt" if y < SW + h - 1 else "grass_block")
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
        building(d, pal, 38, 3, 46, 11, 3, (42, 3, "north"), L, "modern")
        furnish(d, "guard", 38, 3, L)
        porch(d, 42, 3, "north", "smooth_stone_slab[type=bottom,waterlogged=false]")
        place(d, [(40, SW, 2, "potted_bamboo"), (44, SW, 2, "potted_bamboo"), (39, SW + 1, 2, "andesite_wall")])
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
        building(d, pal, 3, 30, 19, 42, 3, (11, 30, "north"), L, "modern")
        furnish(d, "depot", 3, 30, L)
        porch(d, 11, 30, "north", "cut_copper_slab[type=bottom,waterlogged=false]" if L >= 5 else "smooth_stone_slab[type=bottom,waterlogged=false]")
        place(d, [(5, SW, 29, "barrel[facing=up,open=false]"), (6, SW, 29, "barrel[facing=north,open=false]"), (17, SW, 29, "andesite_wall"), (17, SW + 1, 29, "lantern[hanging=false,waterlogged=false]")])
        d.fill(3, GY, 26, 19, GY, 29, "polished_andesite")
        for x in range(4, 19, 3):
            d.set(x, GY, 27, "yellow_concrete")
        pal2 = dict(wall="mangrove_planks", wall2="white_terracotta", plinth="deepslate_tiles", trim="deepslate_tiles",
                    floor="mangrove_planks", roof="deepslate_tile", roofblock="deepslate_tiles",
                    parapet="deepslate_tiles", accent="magenta_terracotta", fin="magenta_concrete",
                    glass="glass_pane", door="mangrove", stairs="mangrove_stairs", rail="mangrove_fence",
                    shutter="mangrove")
        building(d, pal2, 3, 3, 11, 11, 3, (7, 11, "south"), L, "modern")
        furnish(d, "comms", 3, 3, L)
        porch(d, 7, 11, "south", "deepslate_tile_slab[type=bottom,waterlogged=false]")
        place(d, [(5, SW, 12, "potted_bamboo"), (9, SW, 12, "potted_bamboo")])
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
        building(d, pal, 32, 32, 50, 48, 6, (41, 32, "north"), L,
                 "modern")
        furnish(d, "hq", 32, 32, L)
        porch(d, 41, 32, "north", "smooth_quartz_slab[type=bottom,waterlogged=false]", "lantern[hanging=true,waterlogged=false]")
        place(d, [(38, SW, 31, "potted_bamboo"), (44, SW, 31, "potted_bamboo"), (36, SW, 31, "andesite_wall"), (46, SW, 31, "andesite_wall")])
        pal3 = dict(wall="white_terracotta", wall2="brown_terracotta", plinth="polished_deepslate",
                    trim="polished_deepslate", floor="birch_planks", roof="deepslate_tile", roofblock="deepslate_tiles",
                    parapet="polished_deepslate", accent="yellow_terracotta", fin="yellow_concrete",
                    glass="glass_pane", door="cherry", stairs="birch_stairs", rail="birch_fence", shutter="cherry")
        building(d, pal3, 3, 45, 17, 53, 3, (10, 45, "north"), L, "modern")
        furnish(d, "barracks", 3, 45, L)
        porch(d, 10, 45, "north", "deepslate_tile_slab[type=bottom,waterlogged=false]")
        for x in range(4, 17, 3):
            if x != 10:
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
        for y in range(GY + 25, GY + 32):
            d.set(mx, y, mz, "iron_bars" if y % 3 else "andesite_wall")
        d.set(mx, GY + 32, mz, "redstone_lamp[lit=true]")
        d.set(mx, GY + 33, mz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        for x in range(34, 45, 3):
            d.set(x, GY + 25, 46, "daylight_detector[inverted=false,power=0]")
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
            d.set(x, GY, z, "grass_block")
            if d.air(x, SW, z):
                d.set(x, SW, z, fl[(x * 3 + z + salt) % len(fl)])


def hearthwood(rel, L):
    P = PLANS["Hearthwood"]
    sx, sy, sz = P["size"]
    d = Design("Hearthwood", rel, (sx, sy, sz), gy=GY, paving="grass_block")
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
        building(d, pal, 40, 3, 50, 11, 2, (45, 11, "south"), L, "tudor", "gable",
                 chimney=(51, 7))
        furnish(d, "cottage", 40, 3, L)
        place(d, [(39, SW, 6, "water_cauldron[level=3]"), (39, SW, 9, "barrel[facing=up,open=false]"),
                  (39, SW, 4, "potted_red_tulip")])
        porch(d, 45, 11, "south", "deepslate_tile_slab[type=bottom,waterlogged=false]")
        window_box(d, 43, GY + 6, 3, "north", "warped", "potted_red_tulip")
        window_box(d, 47, GY + 6, 3, "north", "warped", "potted_allium")
        shutters(d, 45, GY + 6, 3, "north", "warped")
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
        building(d, pal, 3, 21, 21, 29, 3, (12, 21, "north"), L, "tudor", "gable",
                 chimney=(2, 25))
        furnish(d, "almshouse", 3, 21, L)
        d.chair(9, SW, 30, "north", "oak", sit=False)
        d.chair(10, SW, 30, "north", "oak", sit=False)
        d.chair(15, SW, 30, "north", "oak", sit=False)
        place(d, [(5, SW, 30, "barrel[facing=up,open=false]"), (12, SW, 30, "potted_azure_bluet"),
                  (19, SW, 30, "water_cauldron[level=3]"), (20, SW, 30, "composter[level=4]")])
        porch(d, 12, 21, "north", "brick_slab[type=bottom,waterlogged=false]")
        window_box(d, 7, GY + 6, 21, "north", "bamboo", "potted_oxeye_daisy")
        window_box(d, 17, GY + 6, 21, "north", "bamboo", "potted_azure_bluet")
        shutters(d, 9, GY + 10, 21, "north", "bamboo")
        shutters(d, 15, GY + 10, 21, "north", "bamboo")
        flowerbed(d, 4, 19, 10, 19, 3)
        flowerbed(d, 14, 19, 20, 19, 4)
        for x in (3, 21):
            lamp_post(d, x, 18, "dark_oak_fence", "lantern[hanging=false,waterlogged=false]", 3)
    if L >= 4:              # smithy: stone and oak frame, spruce shingles, yellow shutters
        pal = dict(wall="stone_bricks", wall2="stone_bricks", plinth="cobblestone", trim="stripped_oak_log",
                   floor="cobblestone", roof="spruce", gable="oak_planks", accent="oak_planks", glass="glass_pane",
                   door="oak", stairs="oak_stairs", rail="oak_fence", shutter="bamboo", chimney="cobblestone")
        building(d, pal, 44, 46, 56, 53, 2, (50, 46, "north"), L, "tudor", "gable", chimney=(57, 49))
        furnish(d, "smithy", 44, 46, L)
        place(d, [(43, SW, 50, "grindstone[face=floor,facing=east]"), (43, SW, 52, "barrel[facing=up,open=false]"),
                  (47, SW, 54, "spruce_log[axis=x]"), (48, SW, 54, "spruce_log[axis=x]"),
                  (52, SW, 54, "barrel[facing=up,open=false]"), (54, SW, 54, "hay_block[axis=y]")])
        porch(d, 50, 46, "north", "spruce_slab[type=bottom,waterlogged=false]")
        d.set(42, SW, 47, "anvil[facing=north]")
        d.set(42, SW, 49, "water_cauldron[level=3]")
        for z in range(19, 54):                            # dry-stone wall along the lane, lamps and benches
            if z in (23, 24, 33, 34, 45, 46):
                continue
            d.set(34, SW, z, "mossy_cobblestone" if H(34, 1, z) < 40 else "cobblestone")
            d.set(34, SW + 1, z, "mossy_cobblestone_wall" if z % 3 else "cobblestone_wall")
        for z in (22, 32, 44):
            lamp_post(d, 35, z, "dark_oak_fence", "lantern[hanging=false,waterlogged=false]", 3)
            d.chair(38, SW, z, "east", "dark_oak", sit=False)
    if L >= 5:              # vicarage: light-blue colour-washed walls, rose granite roof, red door
        pal = dict(wall="light_blue_terracotta", wall2="white_terracotta", plinth="stone_bricks",
                   trim="stripped_dark_oak_log", floor="oak_planks", roof="granite", gable="white_terracotta",
                   accent="dark_oak_planks", glass="glass_pane", door="crimson", stairs="dark_oak_stairs",
                   rail="dark_oak_fence", shutter="warped", chimney="bricks")
        building(d, pal, 3, 41, 15, 51, 3, (9, 41, "north"), L, "tudor", "gable",
                 chimney=(2, 46))
        furnish(d, "vicarage", 3, 41, L)
        porch(d, 9, 41, "north", "granite_slab[type=bottom,waterlogged=false]")
        window_box(d, 5, GY + 6, 41, "north", "warped", "potted_red_tulip")
        window_box(d, 13, GY + 6, 41, "north", "warped", "potted_pink_tulip")
        shutters(d, 7, GY + 10, 41, "north", "warped")
        shutters(d, 11, GY + 10, 41, "north", "warped")
        pal = dict(wall="yellow_terracotta", wall2="yellow_terracotta", plinth="stone_bricks", trim="stripped_oak_log",
                   floor="oak_planks", roof="dark_prismarine", gable="yellow_terracotta", accent="oak_planks",
                   glass="glass_pane", door="warped", stairs="oak_stairs", rail="oak_fence", shutter="mangrove",
                   chimney="bricks")
        building(d, pal, 52, 3, 59, 12, 3, (55, 12, "south"), L, "tudor", "gable",
                 chimney=(60, 7))
        furnish(d, "lodge", 52, 3, L)
        porch(d, 55, 12, "south", "dark_prismarine_slab[type=bottom,waterlogged=false]")
        shutters(d, 57, GY + 6, 12, "south", "mangrove")
        flowerbed(d, 52, 13, 54, 14, 7)
        flowerbed(d, 57, 13, 59, 14, 8)
        for x in range(1, 20):                             # churchyard hedge and yews round the vicarage garden
            if x not in (9, 10):
                d.set(x, SW, 53, "oak_leaves[distance=7,persistent=true,waterlogged=false]")
                d.set(x, SW + 1, 53, "oak_leaves[distance=7,persistent=true,waterlogged=false]")
        for z in range(40, 53):
            d.set(18, SW, z, "oak_leaves[distance=7,persistent=true,waterlogged=false]")
        for (tx, tz) in ((17, 37), (1, 37)):
            tree(d, tx, tz, SW, "spruce", 5)
        flowerbed(d, 3, 39, 7, 39, 5)
        flowerbed(d, 11, 39, 15, 39, 6)
    if L >= 5:              # tithe barn (mud brick and oak frame, brown tile roof) and the bell tower
        pal = dict(wall="mud_bricks", wall2="white_terracotta", plinth="cobblestone", trim="stripped_oak_log",
                   floor="spruce_planks", roof="mud_brick", gable="white_terracotta", accent="oak_planks",
                   glass="glass_pane", door="crimson", stairs="spruce_stairs", rail="spruce_fence",
                   shutter="crimson", chimney="cobblestone")
        building(d, pal, 40, 32, 56, 42, 4, (48, 32, "north"), L, "tudor",
                 "gable")
        furnish(d, "barn", 40, 32, L)
        porch(d, 48, 32, "north", "mud_brick_slab[type=bottom,waterlogged=false]")
        place(d, [(44, SW, 31, "hay_block[axis=y]"), (45, SW, 31, "hay_block[axis=x]"), (52, SW, 31, "barrel[facing=up,open=false]")])
        for (tx, tz) in ((44, 15), (50, 15), (56, 18), (20, 47), (24, 52), (28, 47), (28, 52), (58, 50), (58, 26)):
            tree(d, tx, tz, SW, "oak" if tx % 2 else "birch", 4)
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
    d = Design("Cascadia", rel, (sx, sy, sz), gy=GY, paving="grass_block")
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
                b = "grass_block" if hh < 60 else "moss_block" if hh < 80 else "coarse_dirt"
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
    for (lx, lz) in ((x0, 5), (x0 + 2, 9)):                  # lamps hung from the adit sets
        d.set(lx, SW + 2, lz, "lantern[hanging=true,waterlogged=false]")
    if L >= 2:              # tool shed: weathered stripped spruce, spruce roof
        pal = dict(wall="stripped_spruce_log", wall2="stripped_spruce_log", plinth="cobblestone", trim="spruce_log",
                   floor="spruce_planks", roof="spruce", gable="spruce_planks", accent="spruce_planks",
                   glass="glass_pane", door="spruce", stairs="spruce_stairs", rail="spruce_fence", shutter="spruce")
        building(d, pal, 2, 18, 9, 25, 1, (5, 18, "north"), L, "timber", "gable")
        furnish(d, "shed", 2, 18, L)
        place(d, [(4, SW + 2, 17, "lantern[hanging=false,waterlogged=false]") if False else (3, SW, 17, "spruce_log[axis=y]")])
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
        building(d, pal, 2, 3, 12, 13, 3, (7, 3, "north"), L, "timber", "gable",
                 chimney=(1, 8))
        furnish(d, "bunkhouse", 2, 3, L)
        place(d, [(3, SW, 14, "barrel[facing=up,open=false]"), (10, SW, 14, "water_cauldron[level=3]"),
                  (11, SW, 14, "potted_fern")])
        d.chair(6, SW, 14, "north", "spruce", sit=False)
        d.chair(7, SW, 14, "north", "spruce", sit=False)
        shutters(d, 5, GY + 6, 3, "north", "mangrove")
        shutters(d, 9, GY + 6, 3, "north", "mangrove")
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
        # open woodshed: four posts under a slab roof, cordwood stacked along the back
        for (px, pz) in ((14, 1), (19, 1), (14, 5), (19, 5)):
            for y in range(SW, SW + 3):
                d.set(px, y, pz, "spruce_log[axis=y]")
        for x in range(13, 21):
            for z in range(0, 7):
                d.set(x, SW + 3, z, "spruce_slab[type=bottom,waterlogged=false]")
        for x in range(15, 19):
            for y in range(SW, SW + 3):
                d.set(x, y, 5, "spruce_log[axis=z]" if (x + y) % 2 else "stripped_spruce_log[axis=z]")
                d.set(x, y, 4, "spruce_log[axis=z]" if (x + y) % 2 == 0 else "oak_log[axis=z]")
        d.set(15, SW, 2, "spruce_log[axis=y]")
        d.set(16, SW, 2, "grindstone[face=floor,facing=north]")
    if L >= 4:              # cookhouse: red mangrove siding, river-rock plinth, green-blue metal roof
        pal = dict(wall="mangrove_planks", wall2="mangrove_planks", plinth="mossy_cobblestone", trim="dark_oak_log",
                   floor="spruce_planks", roof="dark_prismarine", gable="mangrove_planks", accent="green_terracotta",
                   glass="glass_pane", door="spruce", stairs="spruce_stairs", rail="spruce_fence", shutter="spruce",
                   chimney="cobblestone")
        building(d, pal, 42, 2, 53, 12, 3, (47, 2, "north"), L, "timber", "gable",
                 chimney=(54, 7))
        furnish(d, "cookhouse", 42, 2, L)
        place(d, [(43, SW, 13, "spruce_log[axis=x]"), (44, SW, 13, "spruce_log[axis=x]"),
                  (46, SW, 13, "barrel[facing=up,open=false]"), (52, SW, 13, "water_cauldron[level=3]")])
        d.chair(49, SW, 13, "north", "spruce", sit=False)
        d.chair(50, SW, 13, "north", "spruce", sit=False)
        porch(d, 47, 2, "north", "dark_prismarine_slab[type=bottom,waterlogged=false]" if L >= 4 else "spruce_slab[type=bottom,waterlogged=false]")
        place(d, [(44, SW, 1, "barrel[facing=up,open=false]"), (50, SW, 1, "water_cauldron[level=3]")])
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
    if L >= 4:              # powder magazine: river-rock walls, stone-brick roof, red barn-paint door trim
        pal = dict(wall="mossy_cobblestone", wall2="cobblestone", plinth="tuff", trim="cobblestone",
                   floor="stone", roof="stone_brick", gable="cobblestone", accent="red_terracotta",
                   glass="iron_bars", door="mangrove", stairs="stone_stairs", rail="spruce_fence", shutter="mangrove")
        building(d, pal, 2, 28, 9, 35, 2, (5, 28, "north"), L, "timber", "gable")
        furnish(d, "magazine", 2, 28, L)
        place(d, [(4, SW + 2, 27, "red_terracotta"), (6, SW + 2, 27, "red_terracotta")])
        for (bx, bz) in ((41, 19), (41, 25)):              # ore bins by the headframe
            for ax in range(3):
                for y in range(SW, SW + 3):
                    d.set(bx - ax, y, bz, "spruce_planks" if y < SW + 2 else "spruce_slab[type=bottom,waterlogged=false]")
            d.set(bx - 1, SW + 2, bz, "gravel")
        for (lx, lz) in ((40, 14), (40, 30), (12, 27), (12, 37), (53, 25), (53, 38)):
            lamp_post(d, lx, lz, "spruce_fence", "lantern[hanging=false,waterlogged=false]", 3)
        for x in range(2, 10):                             # split-rail fence round the magazine yard
            d.set(x, SW, 37, "spruce_fence")
        for z in range(26, 38):                            # rail spur to the magazine
            d.set(10, SW, z, "rail[shape=north_south,waterlogged=false]")
            d.set(10, GY, z, "gravel")
        d.set(11, SW, 36, "barrel[facing=up,open=false]")
        for x in range(10, 18):
            d.set(x, SW, 38, "spruce_fence")
        for (ax, az) in ((36, 3), (38, 3), (36, 5), (38, 5)):  # water tank on timber stilts by the cookhouse
            for y in range(SW, SW + 4):
                d.set(ax, y, az, "spruce_log[axis=y]")
        for y in (SW + 4, SW + 5):
            for ax in range(36, 39):
                for az in range(3, 6):
                    d.set(ax, y, az, "spruce_planks" if y == SW + 4 else "stripped_spruce_wood[axis=y]")
        d.set(37, SW + 6, 4, "spruce_slab[type=bottom,waterlogged=false]")
        for x in range(11, 14):                            # cordwood stack by the magazine
            for z in (29, 30, 31):
                for y in range(SW, SW + 2):
                    d.set(x, y, z, "spruce_log[axis=z]" if (x + y) % 2 else "stripped_spruce_log[axis=z]")
    if L >= 4:              # hoist house by the headframe: dark oak, slate roof, mustard trim
        pal = dict(wall="dark_oak_planks", wall2="dark_oak_planks", plinth="andesite", trim="stripped_spruce_log",
                   floor="spruce_planks", roof="deepslate_tile", gable="dark_oak_planks", accent="yellow_terracotta",
                   glass="glass_pane", door="spruce", stairs="spruce_stairs", rail="spruce_fence", shutter="spruce",
                   chimney="cobblestone")
        building(d, pal, 42, 27, 52, 35, 4, (47, 27, "north"), L, "timber",
                 "gable")
        furnish(d, "hoist", 42, 27, L)
        porch(d, 47, 27, "north", "deepslate_tile_slab[type=bottom,waterlogged=false]")
    if L >= 5:              # general store & assay office: rose cherry siding, red cedar roof, green trim
        pal = dict(wall="cherry_planks", wall2="stripped_spruce_log", plinth="mossy_cobblestone",
                   trim="spruce_log", floor="spruce_planks", roof="mangrove", gable="cherry_planks",
                   accent="green_terracotta", glass="glass_pane", door="spruce", stairs="spruce_stairs",
                   rail="spruce_fence", shutter="spruce", chimney="cobblestone")
        building(d, pal, 38, 44, 52, 56, 4, (45, 44, "north"), L, "timber", "gable",
                 chimney=(53, 50))
        furnish(d, "store", 38, 44, L)
        porch(d, 45, 44, "north", "mangrove_slab[type=bottom,waterlogged=false]")
        place(d, [(42, SW, 43, "barrel[facing=up,open=false]"), (43, SW, 43, "hay_block[axis=y]"), (48, SW, 43, "spruce_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")])
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
        building(d, pal, 2, 42, 16, 54, 4, (9, 42, "north"), L, "timber", "gable")
        furnish(d, "mill", 2, 42, L)
        porch(d, 9, 42, "north", "spruce_slab[type=bottom,waterlogged=false]")
        place(d, [(5, SW, 41, "white_wool"), (6, SW, 41, "white_wool"), (13, SW, 41, "barrel[facing=up,open=false]")])
        # meeting hall: stripped logs with dark-oak trim under a teal (weathered copper look) roof
        pal = dict(wall="stripped_spruce_log", wall2="dark_oak_planks", plinth="tuff", trim="dark_oak_log",
                   floor="spruce_planks", roof="warped", gable="stripped_spruce_log", accent="dark_oak_planks",
                   glass="glass_pane", door="dark_oak", stairs="dark_oak_stairs", rail="dark_oak_fence",
                   shutter="dark_oak", chimney="cobblestone")
        building(d, pal, 19, 40, 35, 54, 3, (27, 40, "north"), L, "timber", "gable",
                 chimney=(36, 47))
        furnish(d, "hall", 19, 40, L)
        porch(d, 27, 40, "north", "warped_slab[type=bottom,waterlogged=false]")
        for x in range(19, 36):
            d.set(x, GY, 38, "spruce_planks")
            d.set(x, GY, 39, "spruce_planks")
        for x in (19, 35):
            lamp_post(d, x, 37, "spruce_fence", "lantern[hanging=false,waterlogged=false]", 3)
        for (tx, tz) in ((37, 40), (53, 40), (17, 57), (36, 58), (53, 59), (1, 39)):
            tree(d, tx, tz, SW, "spruce", 6)
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
