"""
Pack-specific bunkers (residence hut with four child huts: canteen, school, clinic, farm office).

  Hearthwood  "Undercroft": brick well-house at the surface, stairs down to a barrel-vaulted brick gallery with
              rooms on both sides (dorm, canteen, school, clinic); farm vault below with a lantern-lit field;
              storage cellars at the bottom (level 3+)
  Cascadia    "Mine refuge": timber mine portal in a rock outcrop, a shaft with stairs, timber-shored tunnels to
              the living caverns, a farm cavern with a field, an ore store and workshop deeper down (level 3+)

Requirements as the Neoterra bunker: dorm with 1 bed per level, canteen 1 furnace per level + smoker + crafting
table + rack + seats, school 10 seats + teacher spot + 2 bookshelves per level, clinic 2 beds per level + furnace
(+ brewing stand from level 3), farm office racks (1 per level) + composter + barrel + seat, and a scarecrow field.

usage: python bunker_styles.py <pack dir> <Hearthwood|Cascadia>
"""
from __future__ import annotations

import sys
from pathlib import Path

from nbtlib import tag as NBT

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from blueprint import Blueprint  # noqa: E402
from common import connect_panes, rack_te  # noqa: E402
from twinbuilder import hut_te, SOLID, SUBST  # noqa: E402

RACK = "minecolonies:blockminecoloniesrack[facing={},variant=blockrackemptysingle]"
DIRS = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}

MAT = {
    "Hearthwood": dict(wall="bricks", wall2="stone_bricks", floor="dark_oak_planks", floor2="bricks", trim="chiseled_stone_bricks",
                       wood="dark_oak", seat="dark_oak_stairs", table="dark_oak_slab[type=top,waterlogged=false]",
                       bed="red", light="lantern[hanging=true,waterlogged=false]", rock="stone_bricks"),
    "Cascadia": dict(wall="cobblestone", wall2="mossy_cobblestone", floor="spruce_planks", floor2="coarse_dirt", trim="spruce_log[axis=y]",
                     wood="spruce", seat="spruce_stairs", table="spruce_slab[type=top,waterlogged=false]",
                     bed="green", light="lantern[hanging=true,waterlogged=false]", rock="stone"),
}
ROCKS = ["stone", "andesite", "tuff", "cobblestone", "mossy_cobblestone"]

# child room interior sizes (x, z) per pack – different shapes per pack
ROOM = {"Hearthwood": {"bunkerkitchen": (11, 9), "bunkerschool": (13, 9), "bunkerclinic": (11, 9), "bunkerfarm": (11, 9)},
        "Cascadia": {"bunkerkitchen": (9, 11), "bunkerschool": (9, 13), "bunkerclinic": (9, 13), "bunkerfarm": (9, 9)}}
CHILD_BLOCK = {"bunkerkitchen": "blockhutcook", "bunkerschool": "blockhutschool",
               "bunkerclinic": "blockhuthospital", "bunkerfarm": "blockhutfarmer"}


def mc(s):
    return s if ":" in s else "minecraft:" + s


class G:
    def __init__(self, sx, sy, sz, name):
        self.bp = Blueprint(sx, sy, sz, name)
        self.sx, self.sy, self.sz = sx, sy, sz

    def S(self, x, y, z, s, te=None):
        if 0 <= x < self.sx and 0 <= y < self.sy and 0 <= z < self.sz:
            self.bp.set(x, y, z, mc(s), te)

    def get(self, x, y, z):
        return self.bp.get(x, y, z)

    def box(self, x1, y1, z1, x2, y2, z2, s):
        for y in range(y1, y2 + 1):
            for z in range(z1, z2 + 1):
                for x in range(x1, x2 + 1):
                    self.S(x, y, z, s)

    def bed(self, x, y, z, facing, colour):
        dx, dz = DIRS[facing]
        self.S(x, y, z, f"{colour}_bed[facing={facing},occupied=false,part=foot]")
        self.S(x + dx, y, z + dz, f"{colour}_bed[facing={facing},occupied=false,part=head]")


# ------------------------------------------------------------------------------------------------ child rooms
def furnish(style, name, g, L, ox, oy, oz, tags):
    """Room interior at (ox, oy, oz) = local (0, 0, 0); the door is always at local (0, 0, sz//2) (west wall)."""
    m = MAT[style]
    sx, sz = ROOM[style][name]
    dz = sz // 2

    def at(x, z, s, dy=0):
        g.S(ox + x, oy + dy, oz + z, s)

    def seat(x, z, back):
        at(x, z, f"{m['seat']}[facing={back},half=bottom,shape=straight,waterlogged=false]")
        tags.setdefault((ox + x, oy, oz + z), []).append("sit")

    if name == "bunkerkitchen":
        for i in range(L):
            at(sx - 1, 1 + i, "furnace[facing=west,lit=false]")
            tags.setdefault((ox + sx - 2, oy, oz + 1 + i), []).append("work")
        at(sx - 1, 1 + L, "smoker[facing=west,lit=false]")
        at(sx - 1, 2 + L, "crafting_table")
        at(sx - 1, sz - 1, RACK.format("west"))
        g.bp.tile_entities[(ox + sx - 1, oy, oz + sz - 1)] = rack_te()
        for tx in range(3, sx - 3, 3):
            for tz in (2, sz - 3):
                at(tx, tz, m["table"].replace("[type=top", "[type=top"))
                seat(tx, tz + 1 if tz == 2 else tz - 1, "south" if tz == 2 else "north")
    elif name == "bunkerschool":
        for x in range(2, sx - 2):
            at(x, sz - 1, "black_concrete" if style == "Hearthwood" else "dark_oak_planks", 1)
        tags.setdefault((ox + sx // 2, oy, oz + sz - 2), []).append("work")
        n = 0
        for z in range(2, sz - 3, 2):
            for x in range(2, sx - 1, 2):
                if n >= 10 or (x, z) == (1, dz):
                    continue
                seat(x, z, "north")
                n += 1
        for i in range(2 * L):
            at(sx - 1, 1 + i % (sz - 3), "bookshelf", i // (sz - 3))
    elif name == "bunkerclinic":
        spots = [(x, 1, "south") for x in range(2, sx, 2)] + [(x, sz - 2, "north") for x in range(2, sx, 2)]
        for x, z, f in spots[: 2 * L]:
            g.bed(ox + x, oy, oz + z, f, "white")
        at(sx - 1, dz, "furnace[facing=west,lit=false]")
        at(sx - 1, dz + 1, "barrel[facing=west,open=false]")
        if L >= 3:
            at(sx - 1, dz - 1, "brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]")
    elif name == "bunkerfarm":
        for i in range(L):
            at(2 + i, 0, RACK.format("south"))
            g.bp.tile_entities[(ox + 2 + i, oy, oz)] = rack_te()
        at(sx - 1, 1, "composter[level=0]")
        at(sx - 1, 2, "barrel[facing=west,open=false]")
        at(sx // 2, sz - 2, m["table"])
        seat(sx // 2, sz - 3, "north")
    for x, z in ((2, 2), (sx - 3, sz - 3)):
        if g.get(ox + x, oy + 3, oz + z) == "minecraft:air":
            g.S(ox + x, oy + 3, oz + z, m["light"])


def child_hut_local(style, name):
    sx, sz = ROOM[style][name]
    return (1, 0, sz // 2 + 2) if name != "bunkerfarm" else (sx - 2, 0, sz - 1)


def build_room(style, name, L):
    sx, sz = ROOM[style][name]
    g = G(sx, 4, sz, f"{name}{L}.blueprint")
    tags = {}
    furnish(style, name, g, L, 0, 0, 0, tags)
    hut = child_hut_local(style, name)
    tags.setdefault(hut, []).append("invisible")
    path = f"fundamentals/{name}{L}.blueprint"
    g.S(*hut, f"minecolonies:{CHILD_BLOCK[name]}[facing=north]", hut_te(style, path, (sx, 4, sz), hut, tags))
    g.bp.primary_offset = hut
    g.bp.architects = [style]
    connect_panes(g.bp)
    return g.bp


# ------------------------------------------------------------------------------------------------ helpers
def field(g, cx, F, cz, half=6, light_y=None, floor="dirt"):
    for x in range(cx - half, cx + half + 1):
        for z in range(cz - half, cz + half + 1):
            if (x, z) == (cx, cz):
                g.S(x, F, z, floor)
                continue
            g.S(x, F, z, "water[level=0]" if (x - cx) % 4 == 2 else "farmland[moisture=7]")
            g.S(x, F + 1, z, "air")
    g.S(cx, F + 1, cz, "minecolonies:blockhutfield[facing=north,half=lower]",
        NBT.Compound({"id": NBT.String("minecolonies:scarecrow"), "Item": NBT.String("")}))
    g.S(cx, F + 2, cz, "minecolonies:blockhutfield[facing=north,half=upper]")
    ly = light_y if light_y else F + 4
    for x in range(cx - half + 1, cx + half, 4):
        for z in range(cz - half + 1, cz + half, 4):
            g.S(x, ly, z, "lantern[hanging=true,waterlogged=false]")


def room_shell(g, style, x1, z1, sx, sz, F, child_regions, name, door_side="west"):
    """Walls around a child room interior x1..x1+sx-1, z1..; region reserved; door in the west wall."""
    m = MAT[style]
    for x in range(x1 - 1, x1 + sx + 1):
        for z in range(z1 - 1, z1 + sz + 1):
            edge = x in (x1 - 1, x1 + sx) or z in (z1 - 1, z1 + sz)
            g.S(x, F, z, m["floor"])
            for y in range(F + 1, F + 5):
                if edge:
                    g.S(x, y, z, m["wall"] if style == "Hearthwood" else ROCKS[(x * 3 + y + z) % len(ROCKS)])
                else:
                    g.S(x, y, z, SUBST)
            g.S(x, F + 5, z, m["wall2"] if style == "Hearthwood" else ROCKS[(x + z) % len(ROCKS)])
    dz = z1 + sz // 2
    for y in (F + 1, F + 2):
        g.S(x1 - 1, y, dz, "air")
    hl = child_hut_local(style, name)
    hut = (x1 + hl[0], F + 1, z1 + hl[2])
    g.S(*hut, f"minecolonies:{CHILD_BLOCK[name]}[facing=north]",
        hut_te(style, f"fundamentals/{name}0.blueprint", (0, 0, 0), hut, {}, child=True))
    child_regions.append((name, x1, F + 1, z1))


# ------------------------------------------------------------------------------------------------ Hearthwood undercroft
def undercroft(L):
    style = "Hearthwood"
    m = MAT[style]
    SX, SY, SZ = 37, 27, 47
    SURF = 21
    g = G(SX, SY, SZ, f"bunker{L}.blueprint")
    for x in range(SX):
        for z in range(SZ):
            for y in range(SY):
                g.S(x, y, z, SOLID if y <= SURF else "air")
            g.S(x, SURF, z, "stone_bricks" if (x + z) % 7 == 0 else SOLID)
    tags = {(0, SURF, 0): ["groundlevel"]}
    regions = []
    # surface: brick well-house over the stair
    wx1, wx2, wz1, wz2 = 15, 21, 2, 9
    for x in range(wx1, wx2 + 1):
        for z in range(wz1, wz2 + 1):
            g.S(x, SURF, z, m["floor2"])
            edge = x in (wx1, wx2) or z in (wz1, wz2)
            for y in range(SURF + 1, SURF + 4):
                g.S(x, y, z, (m["wall"] if (y - SURF) != 2 or (x + z) % 2 else "glass_pane") if edge else "air")
    for k in range(4):                                          # pyramid roof
        for x in range(wx1 - 1 + k, wx2 + 2 - k):
            for z in range(wz1 - 1 + k, wz2 + 2 - k):
                if x in (wx1 - 1 + k, wx2 + 1 - k) or z in (wz1 - 1 + k, wz2 + 1 - k):
                    g.S(x, SURF + 4 + k, z, "deepslate_tiles" if L >= 4 else "dark_oak_planks")
    g.S(18, SURF + 1, wz1, "dark_oak_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
    g.S(18, SURF + 2, wz1, "dark_oak_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
    # levels: U1 living (y15), U2 farm (y9, L2+), U3 cellars (y3, L3+)
    U1, U2, U3 = 15, 9, 3
    levels = [U1] + ([U2] if L >= 2 else []) + ([U3] if L >= 3 else [])
    # stair: from the well-house (z3..) down along x 18, one flight per level
    def flight(ytop, ybot, z0):
        for i in range(ytop - ybot):
            z = z0 + i
            y = ytop - i
            g.S(18, y - 1, z, "stone_bricks")
            g.S(18, y, z, "stone_brick_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")
            for yy in range(y + 1, y + 4):
                g.S(18, yy, z, "air")
            for xx in (17, 19):
                for yy in range(y, y + 4):
                    if g.get(xx, yy, z) in ("structurize:blocksolidsubstitution",):
                        g.S(xx, yy, z, "stone_bricks")
        return z0 + (ytop - ybot)
    zend = flight(SURF, U1, 4)
    # U1 gallery: barrel vault along z, x 16..20, z zend..44
    gz1, gz2 = zend, 44
    def gallery(F, z1, z2, lit=True):
        for z in range(z1, z2 + 1):
            for x in range(14, 23):
                g.S(x, F, z, m["floor2"] if x in (14, 22) else (m["floor"] if 16 <= x <= 20 else m["wall2"]))
                for y in range(F + 1, F + 6):
                    inner = 16 <= x <= 20 and (y <= F + 3 or (y == F + 4 and 17 <= x <= 19))
                    if inner:
                        g.S(x, y, z, "air")
                    elif x in (15, 21) and y <= F + 3 or (y == F + 4 and x in (16, 20)) or (y == F + 5 and 17 <= x <= 19):
                        g.S(x, y, z, m["wall"] if (z % 4) else m["trim"])
            if lit and z % 5 == 0:
                g.S(18, F + 4, z, m["light"])
    gallery(U1, gz1, gz2)
    # rooms off the gallery (child rooms west/east) + dorm (parent hut)
    ks = ROOM[style]["bunkerkitchen"]; ss = ROOM[style]["bunkerschool"]; cs = ROOM[style]["bunkerclinic"]
    room_shell(g, style, 23, 14, ks[0], ks[1], U1, regions, "bunkerkitchen")
    room_shell(g, style, 23, 27, cs[0], cs[1], U1, regions, "bunkerclinic")
    room_shell(g, style, 23, 37, ss[0], ss[1], U1, regions, "bunkerschool")
    # doors into the child rooms from the gallery: open the gallery wall at the room door
    for z in (14 + ks[1] // 2, 27 + cs[1] // 2, 37 + ss[1] // 2):
        for y in (U1 + 1, U1 + 2):
            g.S(21, y, z, "air")
            g.S(22, y, z, "air")
    # dorm (parent hut) west of the gallery
    dx1, dx2, dz1, dz2 = 3, 13, 14, 26
    for x in range(dx1 - 1, dx2 + 2):
        for z in range(dz1 - 1, dz2 + 2):
            edge = x in (dx1 - 1, dx2 + 1) or z in (dz1 - 1, dz2 + 1)
            g.S(x, U1, z, m["floor"])
            for y in range(U1 + 1, U1 + 5):
                g.S(x, y, z, m["wall"] if edge else "air")
            g.S(x, U1 + 5, z, m["wall2"])
    for y in (U1 + 1, U1 + 2):
        for x in (14, 15):
            g.S(x, y, 20, "air")
    for i in range(L):
        g.bed(dx1 + 1 + 2 * i, U1 + 1, dz2 - 1, "south", m["bed"])
    for x in range(dx1 + 2, dx2 - 1, 3):
        g.S(x, U1 + 1, dz1 + 3, m["table"])
        g.S(x, U1 + 1, dz1 + 2, f"{m['seat']}[facing=north,half=bottom,shape=straight,waterlogged=false]")
        tags[(x, U1 + 1, dz1 + 2)] = ["sit"]
    g.S(dx1, U1 + 1, dz1 + 1, "barrel[facing=up,open=false]")
    g.S(dx1, U1 + 1, dz1 + 2, "crafting_table")
    g.S(dx1, U1 + 1, dz1 + 3, "furnace[facing=east,lit=false]")
    for x in range(dx1 + 2, dx2, 4):
        g.S(x, U1 + 4, (dz1 + dz2) // 2, m["light"])
    hut = (dx2 - 1, U1 + 1, dz1 + 1)
    if L >= 2:                                                  # stair down to the farm vault at the gallery end
        z = flight(U1, U2, 34)
        gallery(U2, 40, 44)
        for z in range(32, 41):                                 # side passage from the stair foot to the field hall
            g.S(16, U2, z, m["floor"])
            for y in range(U2 + 1, U2 + 4):
                g.S(16, y, z, "air")
        field(g, 18, U2, 25, half=6, light_y=U2 + 4, floor=m["floor"])
        for x in range(11, 26):
            for z in range(18, 33):
                if 12 <= x <= 24 and 19 <= z <= 31:
                    for y in range(U2 + 2, U2 + 4):
                        if g.get(x, y, z) != "minecraft:air":
                            g.S(x, y, z, "air")
                    g.S(x, U2 + 5, z, m["wall2"])
                elif g.get(x, U2 + 1, z) == SOLID:
                    for y in range(U2 + 1, U2 + 5):
                        g.S(x, y, z, m["wall"])
        fs = ROOM[style]["bunkerfarm"]
        room_shell(g, style, 24, 36, fs[0], fs[1], U2, regions, "bunkerfarm")
        for y in (U2 + 1, U2 + 2):
            g.S(21, y, 36 + fs[1] // 2, "air")
            g.S(22, y, 36 + fs[1] // 2, "air")
    if L >= 3:                                                  # storage cellars below the farm vault
        for x in range(4, 33):
            for z in range(36, 47):
                edge = x in (4, 32) or z in (36, 46)
                g.S(x, U3, z, m["floor2"])
                for y in range(U3 + 1, U3 + 5):
                    g.S(x, y, z, m["wall"] if edge else "air")
                g.S(x, U3 + 5, z, m["wall2"])
        for i in range(U2 - U3):                                # stair down from the farm vault gallery
            z = 40 + i
            y = U2 - i
            g.S(20, y, z, "stone_brick_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")
            for yy in range(y + 1, y + 4):
                g.S(20, yy, z, "air")
        for x in range(6, 31, 2):
            if abs(x - 20) > 1:
                for y in range(U3 + 1, U3 + 1 + min(3, L - 1)):
                    g.S(x, y, 37, "barrel[facing=south,open=false]")
        for x in range(6, 31, 6):
            g.S(x, U3 + 4, 41, m["light"])
    tags[hut] = ["hearthwood"]
    connect_panes(g.bp)
    path = f"fundamentals/bunker{L}.blueprint"
    g.S(*hut, "minecolonies:blockhutcitizen[facing=north]", hut_te(style, path, (SX, SY, SZ), hut, tags))
    g.bp.primary_offset = hut
    g.bp.architects = [style]
    g.bp.regions = regions
    return g.bp


# ------------------------------------------------------------------------------------------------ Cascadia mine refuge
def mine_refuge(L):
    style = "Cascadia"
    m = MAT[style]
    SX, SY, SZ = 43, 28, 39
    SURF = 22
    g = G(SX, SY, SZ, f"bunker{L}.blueprint")
    for x in range(SX):
        for z in range(SZ):
            for y in range(SY):
                g.S(x, y, z, SOLID if y <= SURF else "air")
    tags = {(0, SURF, 0): ["groundlevel"]}
    regions = []
    # surface: rock outcrop with a timbered mine portal and a little headframe
    cx, cz = 21, 6
    for x in range(cx - 6, cx + 7):
        for z in range(cz - 3, cz + 6):
            h = 5 - (abs(x - cx) + max(0, abs(z - cz - 1) - 1)) // 2
            for y in range(SURF + 1, SURF + 1 + max(0, h)):
                g.S(x, y, z, ROCKS[(x * 5 + y * 3 + z) % len(ROCKS)])
    for y in range(SURF + 1, SURF + 4):
        for z in range(cz - 3, cz + 4):
            g.S(cx, y, z, "air")
    for x in (cx - 1, cx + 1):
        for y in range(SURF + 1, SURF + 4):
            g.S(x, y, cz - 3, "spruce_log[axis=y]")
    for x in range(cx - 1, cx + 2):
        g.S(x, SURF + 4, cz - 3, "spruce_log[axis=x]")
    for y in range(SURF + 4, SURF + 10):                        # headframe over the shaft
        g.S(cx - 2, y, cz + 2, "spruce_log[axis=y]")
        g.S(cx + 2, y, cz + 2, "spruce_log[axis=y]")
    for x in range(cx - 2, cx + 3):
        g.S(x, SURF + 10, cz + 2, "spruce_log[axis=x]")
    g.S(cx, SURF + 9, cz + 2, "chain[axis=y,waterlogged=false]")
    # main decline: stairs from the portal down to the living level
    U1, U2, U3 = 16, 10, 4
    levels = [U1] + ([U2] if L >= 2 else []) + ([U3] if L >= 3 else [])

    def decline(x, ytop, ybot, z0):
        for i in range(ytop - ybot):
            z = z0 + i
            y = ytop - i
            g.S(x, y, z, "spruce_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")
            for yy in range(y + 1, y + 4):
                g.S(x, yy, z, "air")
            for xx in (x - 1, x + 1):
                for yy in range(y, y + 4):
                    if g.get(xx, yy, z) == SOLID:
                        g.S(xx, yy, z, ROCKS[(xx + yy + z) % len(ROCKS)])
            if i % 3 == 0:                                      # timber sets
                g.S(x - 1, y + 1, z, "spruce_log[axis=y]"); g.S(x + 1, y + 1, z, "spruce_log[axis=y]")
        return z0 + (ytop - ybot)

    z = decline(cx, SURF, U1, cz + 3)

    def tunnel(F, x1, z1, x2, z2, width=3):
        """Timber-shored tunnel along x or z."""
        along_x = abs(x2 - x1) >= abs(z2 - z1)
        rng = range(min(x1, x2), max(x1, x2) + 1) if along_x else range(min(z1, z2), max(z1, z2) + 1)
        for t in rng:
            for w in range(-(width // 2), width // 2 + 1):
                x, zz = (t, z1 + w) if along_x else (x1 + w, t)
                g.S(x, F, zz, m["floor2"] if w else m["floor"])
                for y in range(F + 1, F + 4):
                    g.S(x, y, zz, "air")
                g.S(x, F + 4, zz, ROCKS[(x + zz) % len(ROCKS)])
            for w in (-(width // 2) - 1, width // 2 + 1):
                x, zz = (t, z1 + w) if along_x else (x1 + w, t)
                for y in range(F + 1, F + 4):
                    if g.get(x, y, zz) == SOLID:
                        g.S(x, y, zz, ROCKS[(x * 3 + y + zz) % len(ROCKS)])
            if t % 4 == 0 and width > 1:
                for w in (-(width // 2), width // 2):
                    x, zz = (t, z1 + w) if along_x else (x1 + w, t)
                    for y in range(F + 1, F + 3):
                        g.S(x, y, zz, "spruce_log[axis=y]")
                for w in range(-(width // 2), width // 2 + 1):
                    x, zz = (t, z1 + w) if along_x else (x1 + w, t)
                    g.S(x, F + 3, zz, "stripped_spruce_log[axis=z]" if along_x else "stripped_spruce_log[axis=x]")

    # U1: crossroads under the decline end
    tunnel(U1, cx, z, cx, 30)                                   # main drift south
    tunnel(U1, 4, 20, 38, 20)                                   # cross drift
    for zz in range(z, 31, 5):
        g.S(cx, U1 + 3, zz, m["light"])
    for xx in range(6, 38, 5):
        g.S(xx, U1 + 3, 20, m["light"])
    ks, ss, cs = ROOM[style]["bunkerkitchen"], ROOM[style]["bunkerschool"], ROOM[style]["bunkerclinic"]
    # rooms: doors (west walls) open onto the drifts
    room_shell(g, style, 28, 7, ks[0], ks[1], U1, regions, "bunkerkitchen")       # NE of crossroads
    room_shell(g, style, 28, 23, cs[0], cs[1], U1, regions, "bunkerclinic")       # SE
    room_shell(g, style, 6, 23, ss[0], ss[1], U1, regions, "bunkerschool")        # SW
    for (rx, rz, size) in ((28, 7, ks), (28, 23, cs)):
        door_z = rz + size[1] // 2
        x0 = rx - 1
        xt = cx + 2 if rx > cx else cx - 2
        for xx in range(min(x0, xt), max(x0, xt) + 1):
            for y in (U1 + 1, U1 + 2):
                g.S(xx, y, door_z, "air")
            g.S(xx, U1, door_z, m["floor"])
    tunnel(U1, 24, 12, 24, 20, width=1)                         # kitchen corridor down to the cross drift
    # school west door: connect from its west side round to the drift via its own tunnel
    tunnel(U1, 4, 20, 4, 23 + ss[1] // 2, width=1)
    for y in (U1 + 1, U1 + 2):
        g.S(5, y, 23 + ss[1] // 2, "air")
    # dorm cavern (parent hut) NW
    dx1, dx2, dz1, dz2 = 5, 15, 8, 16
    for x in range(dx1 - 1, dx2 + 2):
        for zz in range(dz1 - 1, dz2 + 2):
            edge = x in (dx1 - 1, dx2 + 1) or zz in (dz1 - 1, dz2 + 1)
            g.S(x, U1, zz, m["floor"])
            for y in range(U1 + 1, U1 + 5):
                g.S(x, y, zz, ROCKS[(x + y * 2 + zz) % len(ROCKS)] if edge else "air")
            g.S(x, U1 + 5, zz, ROCKS[(x + zz) % len(ROCKS)])
    for x in range(dx1 + 2, dx2, 4):                            # roof timbers
        for zz in range(dz1, dz2 + 1):
            g.S(x, U1 + 4, zz, "stripped_spruce_log[axis=z]")
    for y in (U1 + 1, U1 + 2):
        for zz in range(dz2 + 1, 20):
            g.S(10, y, zz, "air")
            g.S(10, U1, zz, m["floor"])
    for i in range(L):
        g.bed(dx1 + 1 + 2 * i, U1 + 1, dz1 + 1, "north", m["bed"])
    for x in range(dx1 + 2, dx2 - 1, 3):
        g.S(x, U1 + 1, dz2 - 2, m["table"])
        g.S(x, U1 + 1, dz2 - 1, f"{m['seat']}[facing=south,half=bottom,shape=straight,waterlogged=false]")
        tags[(x, U1 + 1, dz2 - 1)] = ["sit"]
    g.S(dx2, U1 + 1, dz1, "barrel[facing=up,open=false]")
    g.S(dx2, U1 + 1, dz1 + 1, "crafting_table")
    g.S(dx2, U1 + 1, dz1 + 2, "furnace[facing=west,lit=false]")
    g.S(10, U1 + 3, 12, m["light"])
    hut = (dx2 - 2, U1 + 1, dz1 + 4)
    if L >= 2:                                                  # farm cavern below (carved first, then the stair)
        for x in range(9, 34):
            for zz in range(24, 37):
                for y in range(U2 + 1, U2 + 5):
                    g.S(x, y, zz, "air" if (10 <= x <= 32 and 25 <= zz <= 35) else ROCKS[(x + y + zz) % len(ROCKS)])
                g.S(x, U2 + 5, zz, ROCKS[(x * 2 + zz) % len(ROCKS)])
                g.S(x, U2, zz, m["floor"])
        field(g, 16, U2, 30, half=5, light_y=U2 + 4, floor=m["floor"])
        fs = ROOM[style]["bunkerfarm"]
        room_shell(g, style, 26, 26, fs[0], fs[1], U2, regions, "bunkerfarm")
        for y in (U2 + 1, U2 + 2):
            g.S(25, y, 26 + fs[1] // 2, "air")
        decline(cx, U1, U2, 26)
        for zz in range(25, 33):                                # keep the drift passable beside the stairway
            for x in (cx - 1, cx + 1):
                for y in (U1 + 1, U1 + 2):
                    if "log" in g.get(x, y, zz):
                        g.S(x, y, zz, "air")
    if L >= 3:                                                  # ore store and workshop deeper down
        for x in range(10, 32):
            for zz in range(4, 14):
                edge = x in (10, 31) or zz in (4, 13)
                g.S(x, U3, zz, m["floor2"])
                for y in range(U3 + 1, U3 + 5):
                    g.S(x, y, zz, ROCKS[(x + y + zz) % len(ROCKS)] if edge else "air")
                g.S(x, U3 + 5, zz, ROCKS[(x + zz) % len(ROCKS)])
        for y in range(U2 + 1, U2 + 4):
            g.S(12, y, 24, "air")
        for i in range(U2 - U3):
            zz = 23 - i
            y = U2 - i
            g.S(12, y, zz, "spruce_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
            for yy in range(y + 1, y + 4):
                g.S(12, yy, zz, "air")
        tunnel(U3, 12, 17, 12, 13, width=1)
        for y in (U3 + 1, U3 + 2):
            g.S(12, y, 13, "air")
        for x in range(14, 30, 2):
            for y in range(U3 + 1, U3 + min(3, L)):
                g.S(x, y, 5, "barrel[facing=south,open=false]")
        for x in range(13, 30, 6):
            g.S(x, U3 + 4, 9, m["light"])
    tags[hut] = ["cascadia"]
    connect_panes(g.bp)
    path = f"fundamentals/bunker{L}.blueprint"
    g.S(*hut, "minecolonies:blockhutcitizen[facing=north]", hut_te(style, path, (SX, SY, SZ), hut, tags))
    g.bp.primary_offset = hut
    g.bp.architects = [style]
    g.bp.regions = regions
    return g.bp


BUILD = {"Hearthwood": undercroft, "Cascadia": mine_refuge}


def assemble(style, bp, L):
    """Bunker with its child rooms pasted in (for checking)."""
    for name, x1, y1, z1 in bp.regions:
        r = build_room(style, name, L)
        for y in range(r.sy):
            for z in range(r.sz):
                for x in range(r.sx):
                    bp.set(x1 + x, y1 + y, z1 + z, r.get(x, y, z))
    return bp


def build_all(root: Path, style: str):
    d = root / "fundamentals"
    d.mkdir(parents=True, exist_ok=True)
    for L in range(1, 6):
        BUILD[style](L).save(d / f"bunker{L}.blueprint")
        for name in CHILD_BLOCK:
            build_room(style, name, L).save(d / f"{name}{L}.blueprint")
    print(f"{style}: own bunker + 4 room types x 5 levels")


if __name__ == "__main__":
    build_all(Path(sys.argv[1]), sys.argv[2])
