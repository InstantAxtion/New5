"""
Shared building blocks for the Neoterra style pack.

- Domum Ornamentum (DO) helpers: DO blocks store their material in a block entity
  ({id: domum_ornamentum:materially_retexturable, textureData: {<component>: <block>}}).
  Component keys and allowed materials were checked against DO 1.21.1 and the official
  MineColonies 1.21 packs.
- MineColonies hut block entity (minecolonies:colonybuilding) with blueprintDataProvider.
- Circular geometry helpers.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

from nbtlib import tag as T

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from blueprint import Blueprint, parse_state, format_state  # noqa: E402

PACK_NAME = "Neoterra"
PACK_TAG = "neoterra"

# ----------------------------------------------------------------------------- DO blocks
K_MAIN = "minecraft:block/oak_planks"        # main material component of every DO block
K_SECOND = "minecraft:block/dark_oak_planks"  # second component (frames/paper walls)
K_LIGHT = "minecraft:block/glowstone"         # light component of framed lights


def do_te(textures: dict[str, str]) -> T.Compound:
    return T.Compound({
        "id": T.String("domum_ornamentum:materially_retexturable"),
        "textureData": T.Compound({k: T.String(v) for k, v in textures.items()}),
    })


class Spec:
    """A block state plus an optional block entity (for DO blocks)."""

    def __init__(self, state: str, textures: dict[str, str] | None = None):
        self.state = state
        self.textures = textures

    def te(self):
        return do_te(self.textures) if self.textures else None


def mc(m: str) -> str:
    return m if ":" in m else "minecraft:" + m


def do_slab(mat, type_="bottom"):
    return Spec(f"domum_ornamentum:vanilla_slab_compat[type={type_},waterlogged=false]", {K_MAIN: mc(mat)})


def do_stairs(mat, facing, half="bottom", shape="straight"):
    return Spec(f"domum_ornamentum:vanilla_stairs_compat[facing={facing},half={half},shape={shape},waterlogged=false]",
                {K_MAIN: mc(mat)})


def do_pillar(mat, column):  # column: pillar_base | pillar_column | pillar_capital
    return Spec(f"domum_ornamentum:blockpillar[column={column}]", {K_MAIN: mc(mat)})


def do_paperwall(frame, center):  # pane-like; side connections are set by connect_panes()
    return Spec("domum_ornamentum:blockpaperwall[east=false,north=false,south=false,west=false,waterlogged=false]",
                {K_MAIN: mc(frame), K_SECOND: mc(center)})


def do_light(frame, center="sea_lantern", kind="fancy_light"):  # fancy_light | center_light | four_light
    return Spec(f"domum_ornamentum:{kind}", {K_MAIN: mc(frame), K_LIGHT: mc(center)})


def put(bp: Blueprint, x, y, z, spec):
    if isinstance(spec, Spec):
        bp.set(x, y, z, spec.state, spec.te())
    else:
        bp.set(x, y, z, spec)


# ----------------------------------------------------------------------------- hut block
def hut_te(path: str, size, hut_pos, tags: dict[tuple[int, int, int], list[str]]) -> T.Compound:
    """Block entity for a MineColonies hut, mirroring the fields in the official 1.21 packs."""
    hx, hy, hz = hut_pos
    sx, sy, sz = size

    def pos(x, y, z):
        return T.Compound({"x": T.Int(x), "y": T.Int(y), "z": T.Int(z)})

    name = Path(path).stem
    tag_list = []
    for (x, y, z), names in sorted(tags.items()):
        tag_list.append(T.Compound({
            "tagPos": pos(x - hx, y - hy, z - hz),
            "tagNameList": T.List[T.Compound]([T.Compound({"tagName": T.String(n)}) for n in names]),
        }))
    return T.Compound({
        "id": T.String("minecolonies:colonybuilding"),
        "mirror": T.Byte(0),
        "inWarehouse": T.Byte(0),
        "colony": T.Int(1),
        "type": T.String("minecraft:"),
        "version": T.Int(0),
        "tagSIze": T.Int(0),
        "Item": T.String(""),
        "pack": T.String(PACK_NAME),
        "path": T.String(path),
        "inventory": T.List[T.Compound]([T.Compound({"empty": T.Byte(1)}) for _ in range(27)]),
        "blueprintDataProvider": T.Compound({
            "corner1": pos(-hx, -hy, -hz),
            "corner2": pos(sx - 1 - hx, sy - 1 - hy, sz - 1 - hz),
            "path": T.String(path),
            "schematicName": T.String(name),
            "posTagMap": T.List[T.Compound](tag_list),
        }),
    })


# ----------------------------------------------------------------------------- geometry
def dist(x, z, c):
    return math.hypot(x - c, z - c)


def toward_center(x, z, c):
    dx, dz = c - x, c - z
    if abs(dx) >= abs(dz):
        return "east" if dx > 0 else "west"
    return "south" if dz > 0 else "north"


def angle(x, z, c):
    return math.degrees(math.atan2(z - c, x - c)) % 360


# ----------------------------------------------------------------------------- finishing
PANE_SUFFIXES = ("glass_pane", "iron_bars", "blockpaperwall")
NO_CONNECT = ("stairs", "slab", "lantern", "rail", "door", "bed", "light", "air", "water", "rod",
              "flower", "azalea", "torch", "carpet", "button", "lever", "pressure_plate", "bulb")


def connect_panes(bp: Blueprint):
    """Panes / DO paper walls do not update their connections when pasted, so set them here."""
    dirs = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}
    for x, y, z, s in list(bp.blocks()):
        name, props = parse_state(s)
        if not name.endswith(PANE_SUFFIXES):
            continue
        for d, (dx, dz) in dirs.items():
            n = parse_state(bp.get(x + dx, y, z + dz))[0]
            ok = n.endswith(PANE_SUFFIXES) or not any(k in n for k in NO_CONNECT)
            if not bp.inside(x + dx, y, z + dz):
                ok = False
            props[d] = "true" if ok else "false"
        props["waterlogged"] = "false"
        bp.grid[y][z][x] = format_state(name, props)
