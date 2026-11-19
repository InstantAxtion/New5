"""
Building kit for Neoterra huts: shells, floors, stairs, canopies, landscaping and the hut /
child-hut / decoration anchors, so each building module only describes what makes it unique.

Coordinates: y 0 foundation (solid substitution), y 1 ground. Front = north (z 0).
"""
from __future__ import annotations

import sys
from pathlib import Path

from nbtlib import tag as T

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    Blueprint, Style, put, hut_te, connect_panes, tree, planter, street_lamp, do_slab, bed, door,
    chair, rack, PACK_NAME, DIRS,
)

SUBST = "structurize:blocksubstitution"


def child_hut_te(path):
    """A level-0 child hut (like the official barracks towers)."""
    zero = T.Compound({"x": T.Int(0), "y": T.Int(0), "z": T.Int(0)})
    return T.Compound({
        "id": T.String("minecolonies:colonybuilding"),
        "mirror": T.Byte(0), "inWarehouse": T.Byte(0), "colony": T.Int(0),
        "type": T.String("minecraft:"), "version": T.Int(0), "tagSIze": T.Int(0), "Item": T.String(""),
        "pack": T.String(PACK_NAME), "path": T.String(path),
        "blueprintDataProvider": T.Compound({
            "corner1": zero, "corner2": zero, "path": T.String(path),
            "schematicName": T.String(Path(path).stem), "pack": T.String(PACK_NAME),
            "posTagMap": T.List[T.Compound]([]),
        }),
    })


def decoration_te(path, name, size, anchor, tags):
    ax, ay, az = anchor
    sx, sy, sz = size

    def pos(x, y, z):
        return T.Compound({"x": T.Int(x), "y": T.Int(y), "z": T.Int(z)})
    tag_list = [T.Compound({"tagPos": pos(x - ax, y - ay, z - az),
                            "tagNameList": T.List[T.Compound]([T.Compound({"tagName": T.String(n)}) for n in names])})
                for (x, y, z), names in sorted(tags.items())]
    return T.Compound({
        "id": T.String("minecolonies:decorationcontroller"),
        "path": T.String(path), "name": T.String(name), "pack": T.String(PACK_NAME),
        "Item": T.String(""), "mirror": T.Byte(0), "rotation": T.Int(0),
        "blueprintDataProvider": T.Compound({
            "corner1": pos(-ax, -ay, -az), "corner2": pos(sx - 1 - ax, sy - 1 - ay, sz - 1 - az),
            "path": T.String(path), "schematicName": T.String(name), "pack": T.String(PACK_NAME),
            "posTagMap": T.List[T.Compound](tag_list),
        }),
    })


def edge(x, z, x1, x2, z1, z2):
    return x in (x1, x2) or z in (z1, z2)


class Kit:
    def __init__(self, name: str, category: str, level: int, size, style_level: int | None = None):
        self.name, self.category, self.L = name, category, level
        self.sx, self.sy, self.sz = size
        self.bp = Blueprint(self.sx, self.sy, self.sz, f"{name}{level}.blueprint")
        self.st = Style(level if style_level is None else style_level)
        self.tags: dict[tuple, list[str]] = {}
        s = self.st
        self.W, self.G, self.T, self.D, self.AC = s.WHITE, s.GLASS, s.TRIM, s.DECK, s.ACCENT
        self.glow, self.band = s.GLOW, s.band

    # ------------------------------------------------------------------ basics
    def set(self, x, y, z, spec):
        put(self.bp, x, y, z, spec)

    def fill(self, x1, y1, z1, x2, y2, z2, spec):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for y in range(min(y1, y2), max(y1, y2) + 1):
                for z in range(min(z1, z2), max(z1, z2) + 1):
                    put(self.bp, x, y, z, spec)

    def tag(self, pos, *names):
        self.tags.setdefault(tuple(pos), []).extend(names)

    def seat(self, x, y, z, back_towards):
        bp = self.bp
        bp.set(x, y, z, f"{self.st.SEAT}[facing={back_towards},half=bottom,shape=straight,waterlogged=false]")
        self.tag((x, y, z), "sit")

    def ground(self, paved=(), default="grass_block[snowy=false]", foundation=True):
        """paved: list of (x1, x2, z1, z2) rectangles of paving."""
        bp = self.bp
        if foundation:
            bp.fill(0, 0, 0, self.sx - 1, 0, self.sz - 1, "structurize:blocksolidsubstitution")
        for x in range(self.sx):
            for z in range(self.sz):
                s = default
                for x1, x2, z1, z2 in paved:
                    if x1 <= x <= x2 and z1 <= z <= z2:
                        s = (self.W if (x in (x1, x2) or z in (z1, z2)) and (x2 - x1) > 3 and (z2 - z1) > 3
                             else ("smooth_stone" if (x + z) % 2 else "polished_andesite"))
                bp.set(x, 1, z, s)

    # ------------------------------------------------------------------ shells
    def box(self, x1, x2, z1, z2, floor_y, top_y, front="north", glass_front=True, windows=True,
            floor=True, roof=True, chamfer=False, roof_mat=None, wall=None):
        """Walls y floor_y+1..top_y-1, slab/roof at top_y, interior floor at floor_y."""
        bp, W, G = self.bp, self.W, self.G
        wall = wall or W
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                e = edge(x, z, x1, x2, z1, z2)
                corner = x in (x1, x2) and z in (z1, z2)
                if chamfer and corner:
                    continue
                if not e:
                    if floor:
                        bp.set(x, floor_y, z, self.st.floor(x, z))
                    if roof:
                        put(bp, x, top_y, z, roof_mat or ("smooth_stone" if self.st.early else self.D))
                    continue
                if roof:
                    bp.set(x, top_y, z, self.band)
                face = ("north" if z == z1 else "south" if z == z2 else "west" if x == x1 else "east")
                along = x - x1 if face in ("north", "south") else z - z1
                for y in range(floor_y + 1, top_y):
                    if corner:
                        s = (self.glow if (self.glow and self.L >= 5) else W)
                    elif y == top_y - 1:
                        s = W
                    elif face == front and glass_front:
                        s = self.st.WOOD if along % 3 == 0 else G
                    elif windows and y in (floor_y + 2, floor_y + 3) and along % 3:
                        s = G
                    else:
                        s = wall
                    bp.set(x, y, z, s)

    def opening(self, x1, y1, z1, x2, y2, z2):
        self.fill(x1, y1, z1, x2, y2, z2, "air")

    def door(self, x, y, z, facing="south"):
        door(self.bp, x, y, z, facing, "birch" if self.st.early else "waxed_copper")

    def stairs(self, x, z0, y0, rise, direction, cut_y=None, rail=True, width=1):
        """Straight run: first step at (x, y0, z0), rising `rise` blocks towards `direction`.
        Fills under the steps, cuts the slab at cut_y above the run and adds a guard rail."""
        bp = self.bp
        dx, dz = DIRS[direction]
        cells = []
        for i in range(rise):
            cx, cz, cy = x + dx * i, z0 + dz * i, y0 + i
            for w in range(width):
                wx, wz = (cx + w * abs(dz), cz + w * abs(dx))
                if cy > y0:
                    for yy in range(y0, cy):
                        bp.set(wx, yy, wz, self.W)
                bp.set(wx, cy, wz, f"{self.st.SEAT}[facing={direction},half=bottom,shape=straight,waterlogged=false]")
                cells.append((wx, cy, wz))
        if cut_y is not None:
            for (wx, cy, wz) in cells:
                if cy < cut_y:
                    bp.set(wx, cut_y, wz, "air")
            if rail:
                side = (1, 0) if dx == 0 else (0, 1)
                for (wx, cy, wz) in cells:
                    if cy < cut_y:
                        rx, rz = wx + side[0] * width, wz + side[1] * width
                        if bp.get(rx, cut_y, rz) != "minecraft:air":
                            put(bp, rx, cut_y + 1, rz, self.st.railing)
        return cells

    def railing_ring(self, x1, x2, z1, z2, y, skip=()):
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if edge(x, z, x1, x2, z1, z2) and (x, z) not in skip:
                    put(self.bp, x, y, z, self.st.railing)

    def canopy(self, x1, x2, z1, z2, y, columns=()):
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                e = edge(x, z, x1, x2, z1, z2)
                self.bp.set(x, y, z, (self.glow or self.band) if e else self.D)
        for cx, cz in columns:
            self.fill(cx, 2, cz, cx, y - 1, cz, self.T)

    def lights(self, x1, x2, z1, z2, ceiling_y, step=4):
        for x in range(x1, x2 + 1, step):
            for z in range(z1, z2 + 1, step):
                self.st.ceiling_light(self.bp, x, ceiling_y, z)

    def landscape(self, trees=(), lamps=(), planters=()):
        """Trees from level 2, lamp spires from level 4, planters from level 3."""
        if self.L >= 2:
            for x, z, *h in trees:
                tree(self.bp, x, 2, z, h=h[0] if h else 3)
        if self.L >= 3:
            for x, y, z in planters:
                planter(self.bp, x, y, z)
        if self.L >= 4:
            for x, z in lamps:
                street_lamp(self.bp, x, 2, z, premium=True)

    def mast(self, x, y, z):
        bp = self.bp
        bp.set(x, y, z, self.T)
        for yy in range(y + 1, min(self.sy - 1, y + 6)):
            bp.set(x, yy, z, "chain[axis=y,waterlogged=false]")
        bp.set(x, min(self.sy - 1, y + 6), z, "lightning_rod[facing=up,powered=false,waterlogged=false]")

    # ------------------------------------------------------------------ anchors
    def finish_hut(self, hut, block, te_id="minecolonies:colonybuilding", extra_tags=None, invisible=False):
        connect_panes(self.bp)
        tags = {hut: ["neoterra"] + (["invisible"] if invisible else []), (0, 1, 0): ["groundlevel"]}
        for p, names in self.tags.items():
            tags.setdefault(p, []).extend(names)
        path = f"{self.category}/{self.name}{self.L}.blueprint"
        self.bp.set(*hut, f"minecolonies:{block}[facing=north]",
                    hut_te(path, (self.sx, self.sy, self.sz), hut, tags, te_id=te_id))
        self.bp.primary_offset = hut
        self.bp.architects = ["Neoterra"]
        return self.bp

    def finish_decoration(self, anchor, ground_y=1):
        connect_panes(self.bp)
        tags = {(0, ground_y, 0): ["groundlevel"]}
        for p, names in self.tags.items():
            tags.setdefault(p, []).extend(names)
        path = f"{self.category}/{self.name}{self.L}.blueprint"
        self.bp.set(*anchor, "minecolonies:decorationcontroller[facing=north,mirror=false,waterlogged=false]",
                    decoration_te(path, f"{self.name}{self.L}", (self.sx, self.sy, self.sz), anchor, tags))
        self.bp.primary_offset = anchor
        self.bp.architects = ["Neoterra"]
        return self.bp

    def child(self, pos, block, path):
        self.bp.set(*pos, f"minecolonies:{block}[facing=north]", child_hut_te(path))
