"""
Put pieces together the way a player would place them, to check that walls, roads, rails, canals... line up.

    import layout
    world = layout.compose([("walls/wallstraight", (0, 0, 0), 0), ("walls/walloutsidecorner", (8, 0, 0), 0),
                            ("walls/wallstraight", (12, 0, 4), 1)], pack_dir_or_dict)
    render.iso(world, 2, "out.png", scale=8)

Each entry: (piece, anchor position in the world, quarter turns clockwise seen from above (0-3)). The piece's
anchor (primary offset) lands on the given position, as with the build tool. `piece` is a rel path (looked up in a
pack directory or in a dict rel -> Blueprint) or a Blueprint. Block states are rotated (facing, axis, rail shapes,
fence/pane/wall sides, sign/banner rotation).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))
from blueprint import AIR, Blueprint, format_state, load, parse_state  # noqa: E402

CW = {"north": "east", "east": "south", "south": "west", "west": "north", "up": "up", "down": "down"}
RAIL = {"north_south": "east_west", "east_west": "north_south", "ascending_north": "ascending_east",
        "ascending_east": "ascending_south", "ascending_south": "ascending_west", "ascending_west": "ascending_north",
        "north_east": "south_east", "south_east": "south_west", "south_west": "north_west", "north_west": "north_east"}


def rot_state(st, k):
    if k % 4 == 0 or st == AIR:
        return st
    name, props = parse_state(st)
    for _ in range(k % 4):
        p = dict(props)
        for key in ("facing", "horizontal_facing"):
            if key in props:
                p[key] = CW.get(props[key], props[key])
        if "axis" in props and props["axis"] in ("x", "z"):
            p["axis"] = "z" if props["axis"] == "x" else "x"
        if "shape" in props and props["shape"] in RAIL:
            p["shape"] = RAIL[props["shape"]]
        if "rotation" in props:
            p["rotation"] = str((int(props["rotation"]) + 4) % 16)
        if all(d in props for d in ("north", "east", "south", "west")):
            p["east"], p["south"], p["west"], p["north"] = props["north"], props["east"], props["south"], props["west"]
        props = p
    return format_state(name, props)


def rotate(bp: Blueprint, k: int) -> tuple[Blueprint, tuple[int, int, int]]:
    """Copy rotated k quarter turns clockwise (seen from above: +x east, +z south). Returns (blueprint, anchor)."""
    k %= 4
    ax, ay, az = bp.primary_offset
    cur, anchor = bp, (ax, ay, az)
    for _ in range(k):
        nb = Blueprint(cur.sz, cur.sy, cur.sx, cur.name)
        for x, y, z, st in cur.blocks():
            # clockwise: (x, z) -> (sz-1-z, x)
            nb.set(cur.sz - 1 - z, y, x, rot_state(st, 1))
        ax, ay, az = anchor
        anchor = (cur.sz - 1 - az, ay, ax)
        cur = nb
    out = cur if k else Blueprint(bp.sx, bp.sy, bp.sz, bp.name)
    if not k:
        for x, y, z, st in bp.blocks():
            out.set(x, y, z, st)
    out.primary_offset = anchor
    return out, anchor


def compose(entries, source, margin=2):
    placed = []
    for piece, (wx, wy, wz), k in entries:
        if isinstance(piece, Blueprint):
            bp = piece
        elif isinstance(source, dict):
            bp = source[piece]
        else:
            bp = load(Path(source) / (piece if piece.endswith(".blueprint") else piece + ".blueprint"))
        rb, (ax, ay, az) = rotate(bp, k)
        placed.append((rb, wx - ax, wy - ay, wz - az))
    x0 = min(o[1] for o in placed) - margin
    y0 = min(o[2] for o in placed)
    z0 = min(o[3] for o in placed) - margin
    x1 = max(o[1] + o[0].sx for o in placed) + margin
    y1 = max(o[2] + o[0].sy for o in placed)
    z1 = max(o[3] + o[0].sz for o in placed) + margin
    world = Blueprint(x1 - x0, y1 - y0, z1 - z0, "layout")
    for rb, ox, oy, oz in placed:
        for x, y, z, st in rb.blocks():
            if st == AIR or "substitution" in st:
                continue
            world.set(x + ox - x0, y + oy - y0, z + oz - z0, st)
    world.primary_offset = (0, 0, 0)
    return world
