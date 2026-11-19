"""
Twin Builders' Yard – one building, two builders.

The main blueprint (fundamentals/twinbuilder1-5) is a builder's hut whose second half is reserved for a
child builder's hut (fundamentals/twinbuilderannex0 -> annex1-5). MineColonies registers every hut block
inside a building's blueprint as a child building, so the colony gets two independent builders sharing
one building – each with its own workshop half, racks and crafting table, and each upgraded on its own.

Designed per pack:
  Neoterra    white glass workshop hall, cyan bands, glowing gantry over the yard, sawtooth glazing
  Hearthwood  long plaster-and-timber carpentry house, brick plinth, twin gables, porch, brick chimney
  Cascadia    timber barn workshop on a river-rock base, gambrel roof, big barn doors, log crane

usage: python twinbuilder.py <out-pack-dir> <Neoterra|Hearthwood|Cascadia>
"""
from __future__ import annotations

import sys
from pathlib import Path

from nbtlib import tag as NBT

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from blueprint import Blueprint  # noqa: E402
from common import connect_panes, rack_te  # noqa: E402

SOLID = "structurize:blocksolidsubstitution"
SUBST = "structurize:blocksubstitution"
MATS = {
    "Neoterra": dict(wall=("white_concrete", "smooth_quartz"), glass=("glass", "light_blue_stained_glass"),
                     post=("white_concrete", "quartz_pillar[axis=y]"), accent=("cyan_concrete", "sea_lantern"),
                     floor=("polished_andesite", "smooth_quartz"), roof=("polished_andesite", "smooth_quartz"),
                     base=("light_gray_concrete", "light_gray_concrete"), apron="smooth_stone", door="birch_door"),
    "Hearthwood": dict(wall=("white_terracotta", "white_terracotta"), glass=("glass", "glass"),
                       post=("stripped_dark_oak_log[axis=y]", "stripped_dark_oak_log[axis=y]"),
                       accent=("orange_terracotta", "orange_terracotta"), floor=("oak_planks", "oak_planks"),
                       roof=("dark_oak", "deepslate_tile"), base=("bricks", "bricks"), apron="stone_bricks",
                       door="dark_oak_door"),
    "Cascadia": dict(wall=("spruce_planks", "spruce_planks"), glass=("glass", "glass"),
                     post=("dark_oak_log[axis=y]", "dark_oak_log[axis=y]"), accent=("red_terracotta", "red_terracotta"),
                     floor=("spruce_planks", "spruce_planks"), roof=("spruce", "dark_oak"),
                     base=("cobblestone", "mossy_cobblestone"), apron="cobblestone", door="spruce_door"),
}


def pos(x, y, z):
    return NBT.Compound({"x": NBT.Int(x), "y": NBT.Int(y), "z": NBT.Int(z)})


def hut_te(style, path, size, hut, tags, child=False):
    hx, hy, hz = hut
    sx, sy, sz = size
    tag_list = [NBT.Compound({"tagPos": pos(x - hx, y - hy, z - hz),
                              "tagNameList": NBT.List[NBT.Compound]([NBT.Compound({"tagName": NBT.String(n)}) for n in ns])})
                for (x, y, z), ns in sorted(tags.items())]
    c1 = pos(0, 0, 0) if child else pos(-hx, -hy, -hz)
    c2 = pos(0, 0, 0) if child else pos(sx - 1 - hx, sy - 1 - hy, sz - 1 - hz)
    return NBT.Compound({
        "id": NBT.String("minecolonies:colonybuilding"), "mirror": NBT.Byte(0), "inWarehouse": NBT.Byte(0),
        "colony": NBT.Int(0 if child else 1), "type": NBT.String("minecraft:"), "version": NBT.Int(0),
        "tagSIze": NBT.Int(0), "Item": NBT.String(""), "pack": NBT.String(style), "path": NBT.String(path),
        "inventory": NBT.List[NBT.Compound]([NBT.Compound({"empty": NBT.Byte(1)}) for _ in range(27)]),
        "blueprintDataProvider": NBT.Compound({
            "corner1": c1, "corner2": c2, "path": NBT.String(path), "schematicName": NBT.String(Path(path).stem),
            "pack": NBT.String(style), "posTagMap": NBT.List[NBT.Compound]([] if child else tag_list),
        }),
    })


RACK = "minecolonies:blockminecoloniesrack[facing={},variant=blockrackemptysingle]"


class Hall:
    def __init__(self, style, L):
        self.s, self.L = style, L
        t = 1 if L >= 4 else 0
        self.m = {k: (v[t] if isinstance(v, tuple) else v) for k, v in MATS[style].items()}
        # proportions per pack: Neoterra wide and tall, Hearthwood compact, Cascadia long and low
        w0, d0, h0, h3 = {"Neoterra": (27, 11, 6, 5), "Hearthwood": (19, 9, 5, 4), "Cascadia": (29, 13, 4, 4)}[style]
        self.W = w0 + 2 * L                            # hall length (x)
        self.D = d0 + (L >= 3) * 2                     # hall depth (z)
        self.H = h0 + (L >= 3) * h3                    # wall height (two floors from level 3)
        self.loft = {"Neoterra": 7, "Hearthwood": 6, "Cascadia": 6}[style]
        self.half = self.W // 2                        # x of the dividing wall
        self.ox, self.oz = 3, 5                        # hall offset inside the plot (yard in front)
        self.sx, self.sz = self.W + 6, self.D + 10
        self.sy = self.H + 14

    # ---- shell ---------------------------------------------------------------
    def shell(self, bp):
        m, W, D, H, ox, oz = self.m, self.W, self.D, self.H, self.ox, self.oz
        for x in range(self.sx):
            for z in range(self.sz):
                bp.set(x, 0, z, SOLID)
                bp.set(x, 1, z, "minecraft:" + m["apron"])
        for x in range(ox, ox + W):
            for z in range(oz, oz + D):
                e = x in (ox, ox + W - 1) or z in (oz, oz + D - 1) or x == ox + self.half
                corner = (x in (ox, ox + W - 1, ox + self.half)) and z in (oz, oz + D - 1)
                bp.set(x, 1, z, "minecraft:" + (m["base"] if e else m["floor"]))
                for y in range(2, H + 2):
                    if not e:
                        bp.set(x, y, z, "minecraft:air")
                        continue
                    along = (x - ox) if z in (oz, oz + D - 1) else (z - oz)
                    if corner or (along % 4 == 0 and x != ox + self.half):
                        s = m["post"]
                    elif y == 2:
                        s = m["base"]
                    elif y in (4, 5) and x != ox + self.half and along % 4 in (1, 2, 3) and y != H + 1:
                        s = m["glass"]
                    elif y == H + 1 or (H > 6 and y == self.loft):
                        s = m["accent"]
                    else:
                        s = m["wall"]
                    bp.set(x, y, z, "minecraft:" + s)
                if H > 6 and not e:                     # loft floor
                    bp.set(x, self.loft, z, "minecraft:" + m["floor"])
        # doors in the front wall, one per half, and a door through the dividing wall
        for cx in (ox + self.half // 2, ox + self.half + (W - self.half) // 2):
            for y, half in ((2, "lower"), (3, "upper")):
                bp.set(cx, y, oz, f"minecraft:{m['door']}[facing=south,half={half},hinge=left,open=false,powered=false]")
        self.roof(bp)

    def roof(self, bp):
        m, W, D, H, ox, oz = self.m, self.W, self.D, self.H, self.ox, self.oz
        y0 = H + 2
        if self.s == "Neoterra":                       # flat deck with sawtooth glazing strips
            for x in range(ox, ox + W):
                for z in range(oz, oz + D):
                    e = x in (ox, ox + W - 1) or z in (oz, oz + D - 1)
                    bp.set(x, y0, z, "minecraft:" + (m["accent"] if e else m["roof"]))
                    if not e and (x - ox) % 5 == 0:
                        for k in (1, 2):
                            bp.set(x, y0 + k, z, "minecraft:" + m["glass"])
                        bp.set(x, y0 + 3, z, "minecraft:" + m["accent"])
            return
        span = D + 2
        for x in range(ox - 1, ox + W + 1):
            for j in range(span):
                i = min(j, span - 1 - j)
                if self.s == "Cascadia":                   # gambrel
                    hgt = 2 * i if i < 2 else 3 + i
                else:
                    hgt = i
                z = oz - 1 + j
                first = j < span - 1 - j
                face = "south" if first else "north"
                mat = m["roof"]
                if j == span - 1 - j:
                    bp.set(x, y0 + hgt, z, "minecraft:dark_oak_planks")
                else:
                    bp.set(x, y0 + hgt, z, f"minecraft:{mat}_stairs[facing={face},half=bottom,shape=straight,waterlogged=false]")
                    for k in range(max(0, hgt - (2 if self.s == "Cascadia" and i < 2 else 1)) + 0, hgt):
                        bp.set(x, y0 + k, z, "minecraft:" + (m["wall"] if x in (ox - 1, ox + W) else "dark_oak_planks"))
                if x in (ox, ox + W - 1, ox + self.half) and oz <= z < oz + D:
                    for k in range(0, hgt):
                        if bp.get(x, y0 + k, z) == "minecraft:air":
                            bp.set(x, y0 + k, z, "minecraft:" + m["wall"])

    # ---- furnishing for one builder half -----------------------------------------
    def furnish(self, bp, x1, x2, hut_tags):
        m, oz, D = self.m, self.oz, self.D
        racks = 2 + 2 * self.L
        z_back = oz + D - 2
        placed = 0
        for x in range(x1 + 1, x2):
            if placed >= racks:
                break
            bp.set(x, 2, z_back, RACK.format("north"), rack_te())
            placed += 1
        if placed < racks:                              # second row on the loft / side wall
            for z in range(oz + 2, z_back):
                if placed >= racks:
                    break
                bp.set(x1 + 1, 2, z, RACK.format("east"), rack_te())
                placed += 1
        bp.set(x2 - 1, 2, oz + 2, "minecraft:crafting_table")
        bp.set(x2 - 2, 2, oz + 2, "minecraft:dark_oak_planks")
        bp.set((x1 + x2) // 2, 4, (oz + z_back) // 2, "minecraft:lantern[hanging=true,waterlogged=false]") \
            if self.H <= 6 else bp.set((x1 + x2) // 2, 5, (oz + z_back) // 2, "minecraft:lantern[hanging=true,waterlogged=false]")
        return (x2 - 1, 2, oz + 3)                      # hut position

    def yard(self, bp):
        m, ox, oz, W = self.m, self.ox, self.oz, self.W
        # timber stacks / crane / gantry in front
        if self.s == "Cascadia":
            for x in range(ox + 2, ox + 8):
                for k in range(3 - abs(x - ox - 5) // 2):
                    bp.set(x, 2 + k, 1, "minecraft:spruce_log[axis=x]")
            for y in range(2, 11):
                bp.set(ox + W - 3, y, 2, "minecraft:dark_oak_log[axis=y]")
            for x in range(ox + W - 7, ox + W - 2):
                bp.set(x, 11, 2, "minecraft:dark_oak_log[axis=x]")
            for y in range(7, 11):
                bp.set(ox + W - 7, y, 2, "minecraft:chain[axis=y,waterlogged=false]")
            bp.set(ox + W - 7, 6, 2, "minecraft:dark_oak_planks")
        elif self.s == "Hearthwood":
            for x in range(ox + 2, ox + W - 2, 3):     # porch posts + roof over the front
                for y in range(2, 5):
                    bp.set(x, y, oz - 3, "minecraft:stripped_dark_oak_log[axis=y]")
            for x in range(ox + 1, ox + W - 1):
                for z in range(oz - 3, oz):
                    bp.set(x, 1, z, "minecraft:oak_planks")
                    bp.set(x, 5, z, f"minecraft:{m['roof']}_slab[type=bottom,waterlogged=false]")
            for y in range(2, self.H + 8):            # brick chimney on the gable end
                for dz in (0, 1):
                    bp.set(ox - 1, y, oz + self.D // 2 + dz, "minecraft:bricks")
            bp.set(ox - 1, self.H + 8, oz + self.D // 2, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        else:                                           # Neoterra glowing gantry over the yard
            for x in (ox + 2, ox + W - 3):
                for y in range(2, 9):
                    bp.set(x, y, 2, "minecraft:" + m["post"])
            for x in range(ox + 2, ox + W - 2):
                bp.set(x, 9, 2, "minecraft:" + m["accent"])
            for y in range(5, 9):
                bp.set(ox + W // 2, y, 2, "minecraft:chain[axis=y,waterlogged=false]")
            bp.set(ox + W // 2, 4, 2, "minecraft:dark_oak_planks")

    def build(self):
        bp = Blueprint(self.sx, self.sy, self.sz, f"twinbuilder{self.L}.blueprint")
        self.shell(bp)
        self.yard(bp)
        ox = self.ox
        hut = self.furnish(bp, ox, ox + self.half, {})
        # annex half: everything inside is the child's – left as substitution in the parent
        ax1, ax2 = ox + self.half + 1, ox + self.W - 2
        az1, az2 = self.oz + 1, self.oz + self.D - 2
        for x in range(ax1, ax2 + 1):
            for z in range(az1, az2 + 1):
                for y in range(2, self.H + 2):
                    bp.set(x, y, z, SUBST)
        child_hut = (ax2, 2, self.oz + 3)
        bp.set(*child_hut, "minecolonies:blockhutbuilder[facing=north]",
               hut_te(self.s, "fundamentals/twinbuilderannex0.blueprint", (0, 0, 0), child_hut, {}, child=True))
        connect_panes(bp)
        tags = {(0, 1, 0): ["groundlevel"], hut: [self.s.lower()]}
        path = f"fundamentals/twinbuilder{self.L}.blueprint"
        bp.set(*hut, "minecolonies:blockhutbuilder[facing=north]",
               hut_te(self.s, path, (self.sx, self.sy, self.sz), hut, tags))
        bp.primary_offset = hut
        bp.architects = [self.s]
        # child (annex) blueprint: exactly the reserved interior, hut at the same spot
        cw, ch, cd = ax2 - ax1 + 1, self.H, az2 - az1 + 1
        cb = Blueprint(cw, ch, cd, f"twinbuilderannex{self.L}.blueprint")
        for x in range(cw):
            for z in range(cd):
                for y in range(ch):
                    cb.set(x, y, z, "minecraft:air")
        H = self.H
        if H > 6:                                       # loft floor continues in the annex
            for x in range(cw):
                for z in range(cd):
                    cb.set(x, self.loft - 2, z, "minecraft:" + self.m["floor"])
            for y in range(0, self.loft - 1):           # ladder to the loft
                cb.set(0, y, cd - 1, "minecraft:ladder[facing=north,waterlogged=false]")
        racks = 2 + 2 * self.L
        chx0, chz0 = child_hut[0] - ax1, child_hut[2] - az1
        spots = []
        if self.s == "Neoterra":                        # free-standing rack island down the middle
            for z in (cd // 2, cd // 2 + 2, cd // 2 - 2):
                spots += [(x, z, "north") for x in range(2, cw - 2)]
        elif self.s == "Cascadia":                      # racks along both side walls
            spots += [(0, z, "east") for z in range(1, cd - 1)]
            spots += [(cw - 1, z, "west") for z in range(cd - 2, 0, -1)]
        else:                                           # back wall, then the side wall
            spots += [(x, cd - 1, "north") for x in range(1, cw)]
            spots += [(cw - 1, z, "west") for z in range(1, cd - 1)]
        placed = 0
        for x, z, f in spots:
            if placed >= racks:
                break
            if (x, z) == (chx0, chz0) or (x == 0 and z == cd - 1) or not (0 <= z < cd):
                continue
            if abs(x - chx0) + abs(z - chz0) == 1:
                continue
            cb.set(x, 0, z, RACK.format(f), rack_te())
            placed += 1
        bench = {"Neoterra": ((1, 1), "minecraft:smooth_stone"), "Cascadia": ((cw // 2, cd - 1), "minecraft:spruce_planks"),
                 "Hearthwood": ((1, 1), "minecraft:dark_oak_planks")}[self.s]
        (bx, bz), bmat = bench
        cb.set(bx, 0, bz, "minecraft:crafting_table")
        cb.set(bx + 1, 0, bz, bmat)
        cb.set(cw // 2, min(ch - 1, 2 if H <= 6 else 3), cd // 2, "minecraft:lantern[hanging=true,waterlogged=false]")
        chx, chy, chz = child_hut[0] - ax1, 0, child_hut[2] - az1
        cpath = f"fundamentals/twinbuilderannex{self.L}.blueprint"
        cb.set(chx, chy, chz, "minecolonies:blockhutbuilder[facing=north]",
               hut_te(self.s, cpath, (cw, ch, cd), (chx, chy, chz), {(chx, chy, chz): ["invisible"]}))
        cb.primary_offset = (chx, chy, chz)
        cb.architects = [self.s]
        return bp, cb


def main():
    root, style = Path(sys.argv[1]), sys.argv[2]
    d = root / "fundamentals"
    d.mkdir(parents=True, exist_ok=True)
    for L in range(1, 6):
        bp, cb = Hall(style, L).build()
        bp.save(d / f"twinbuilder{L}.blueprint")
        cb.save(d / f"twinbuilderannex{L}.blueprint")
    print(f"{style}: twin builder 1-5 + annex 1-5")


if __name__ == "__main__":
    main()
