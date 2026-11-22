"""
Full plot from level 1, tight to the building: every level of an upgradable building gets the plot of its biggest
level, which is the area its blocks actually use plus ONE free block all round (MARGIN). Empty plot space the
design left around the building is cut away.

Full plot from level 1: every level of an upgradable building gets the size of its biggest level.

For each hut series (name1..name5 in one folder) the extent of all levels around the hut block is merged (MineColonies
keeps the hut in place when it upgrades), and every level is padded to that box: earth substitution below the
ground, the pack's own paving on the ground, air above. So placing level 1 already clears and reserves the space the
building will need, and the building's borders (hut corners) cover the full plot.

Not padded: child parts (wings, flats, keeps, bunker rooms, twin-builder annex) – they must fit their parent's
reserved space exactly – and mine shafts / quarries, whose size is the area MineColonies digs.

usage: python plotmax.py <pack dir>
"""
from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from nbtlib import tag as NBT

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from blueprint import Blueprint, load, AIR  # noqa: E402

SOLID = "structurize:blocksolidsubstitution"
CHILD = re.compile(r"(wing|annex|flat|barrackstower|bunkerkitchen|bunkerschool|bunkerclinic|bunkerfarm)\d\.blueprint$")
SKIP_DIRS = ("/mineshafts/",)
MARGIN = 1
GROUND_KEEP = ("water", "lava", "farmland", "composted", "hut", "substitution")


def hut_info(bp):
    hx, hy, hz = bp.primary_offset
    te = bp.tile_entities.get((hx, hy, hz))
    if te is None or "blueprintDataProvider" not in te:
        return None
    return te


def ground_y(bp, te):
    hx, hy, hz = bp.primary_offset
    for t in te["blueprintDataProvider"].get("posTagMap", []):
        if any(str(n["tagName"]) == "groundlevel" for n in t["tagNameList"]):
            return int(t["tagPos"]["y"]) + hy
    return 1


def tag_cells(te):
    out = []
    for t in te["blueprintDataProvider"].get("posTagMap", []):
        p = t["tagPos"]
        out.append((int(p["x"]), int(p["y"]), int(p["z"])))
    return out


def content_box(bp):
    """Horizontal extent (hut-relative) of what the building uses: everything above the ground layer, ground cells
    that are not plain paving (water, fields, hut blocks, reserved child space), anything dug or built below the
    ground, tile entities and tags."""
    te = hut_info(bp)
    gy = ground_y(bp, te)
    hx, hy, hz = bp.primary_offset
    xs, zs = [], []
    for y in range(bp.sy):
        layer = bp.grid[y]
        if y > gy:
            fill = AIR
        else:
            fill = Counter(st for row in layer for st in row).most_common(1)[0][0]
        for z in range(bp.sz):
            row = layer[z]
            for x in range(bp.sx):
                st = row[x]
                if st == fill:
                    continue
                if y == gy and not any(k in st for k in GROUND_KEEP):
                    continue
                xs.append(x)
                zs.append(z)
    for (x, _y, z) in bp.tile_entities:
        xs.append(x)
        zs.append(z)
    for (x, _y, z) in tag_cells(te):
        xs.append(x + hx)
        zs.append(z + hz)
    return min(xs) - hx, max(xs) - hx, min(zs) - hz, max(zs) - hz


def pad(bp, box):
    """box = (minx, miny, minz, maxx, maxy, maxz) relative to the hut."""
    hx, hy, hz = bp.primary_offset
    minx, miny, minz, maxx, maxy, maxz = box
    sx, sy, sz = maxx - minx + 1, maxy - miny + 1, maxz - minz + 1
    if (sx, sy, sz) == (bp.sx, bp.sy, bp.sz) and (hx, hy, hz) == (-minx, -miny, -minz):
        return False
    te = hut_info(bp)
    gy_old = ground_y(bp, te)
    # paving: most common block on the ground layer along the old border
    ring = Counter()
    for x in range(bp.sx):
        for z in range(bp.sz):
            if x in (0, bp.sx - 1) or z in (0, bp.sz - 1):
                s = bp.get(x, gy_old, z)
                if s != AIR and "substitution" not in s:
                    ring[s] += 1
    paving = ring.most_common(1)[0][0] if ring else SOLID
    dx, dy, dz = -minx - hx, -miny - hy, -minz - hz          # shift of old content into the new box
    gy = gy_old + dy
    nb = Blueprint(sx, sy, sz, bp.name)
    for y in range(sy):
        fill = SOLID if y < gy else (paving if y == gy else AIR)
        for z in range(sz):
            row = nb.grid[y][z]
            for x in range(sx):
                row[x] = fill
    for y in range(bp.sy):
        for z in range(bp.sz):
            if not 0 <= z + dz < sz:
                continue
            src = bp.grid[y][z]
            dst = nb.grid[y + dy][z + dz]
            for x in range(bp.sx):
                if 0 <= x + dx < sx:
                    dst[x + dx] = src[x]
    nb.tile_entities = {(x + dx, y + dy, z + dz): t for (x, y, z), t in bp.tile_entities.items()
                        if 0 <= x + dx < sx and 0 <= z + dz < sz}
    from blueprint import shift_entities
    nb.entities = shift_entities(getattr(bp, "entities", []), dx, dy, dz, sx, sy, sz)
    nb.primary_offset = (hx + dx, hy + dy, hz + dz)
    nb.architects = getattr(bp, "architects", [])
    hut = nb.tile_entities[nb.primary_offset]
    bdp = hut["blueprintDataProvider"]
    px, py, pz = nb.primary_offset
    bdp["corner1"] = NBT.Compound({"x": NBT.Int(-px), "y": NBT.Int(-py), "z": NBT.Int(-pz)})
    bdp["corner2"] = NBT.Compound({"x": NBT.Int(sx - 1 - px), "y": NBT.Int(sy - 1 - py), "z": NBT.Int(sz - 1 - pz)})
    return nb


def main():
    root = Path(sys.argv[1])
    series = defaultdict(dict)
    for f in root.rglob("*.blueprint"):
        p = f.as_posix()
        m = re.match(r"(.*?)(\d)\.blueprint$", f.name)
        if not m or CHILD.search(f.name) or any(k in p for k in SKIP_DIRS):
            continue
        series[(f.parent, m.group(1))][int(m.group(2))] = f
    padded = 0
    for (folder, base), levels in sorted(series.items()):
        if not levels:
            continue
        bps = {}
        for L, f in levels.items():
            bp = load(f)
            if hut_info(bp) is None:
                bps = {}
                break
            bps[L] = bp
        if not bps:
            continue
        box = [0, 0, 0, 0, 0, 0]
        for bp in bps.values():
            hx, hy, hz = bp.primary_offset
            x1, x2, z1, z2 = content_box(bp)
            box = [min(box[0], x1 - MARGIN), min(box[1], -hy), min(box[2], z1 - MARGIN),
                   max(box[3], x2 + MARGIN), max(box[4], bp.sy - 1 - hy), max(box[5], z2 + MARGIN)]
        for L, bp in bps.items():
            nb = pad(bp, box)
            if nb:
                nb.save(levels[L])
                padded += 1
    print(f"{root.name}: {padded} levels fitted to their building's plot (+1 block margin)")


if __name__ == "__main__":
    main()
