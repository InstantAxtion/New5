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
def hut_te(path: str, size, hut_pos, tags: dict[tuple[int, int, int], list[str]],
           te_id: str = "minecolonies:colonybuilding") -> T.Compound:
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
        "id": T.String(te_id),
        "mirror": T.Byte(0),
        "inWarehouse": T.Byte(0),
        "colony": T.Int(1),
        "type": T.String(te_id if te_id != "minecolonies:colonybuilding" else "minecraft:"),
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


RACK_STATE = "minecolonies:blockminecoloniesrack[facing={facing},variant=blockrackemptysingle]"


def rack_te() -> T.Compound:
    """Block entity of a single (non-double) MineColonies rack, as in the official 1.21 packs."""
    return T.Compound({
        "id": T.String("minecolonies:rack"),
        "tagSIze": T.Int(0),
        "Item": T.String(""),
        "inWarehouse": T.Byte(0),
        "main": T.Byte(0),
        "version": T.Byte(0),
        "pos": T.Compound({"x": T.Int(0), "y": T.Int(0), "z": T.Int(0)}),
        "inventory": T.List[T.Compound]([T.Compound({"empty": T.Byte(1)}) for _ in range(27)]),
    })


def rack(bp, x, y, z, facing="north"):
    bp.set(x, y, z, RACK_STATE.format(facing=facing), rack_te())


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
PANE_SUFFIXES = ("glass_pane", "iron_bars", "blockpaperwall", "_fence")
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


# ----------------------------------------------------------------------------- Neoterra style
# Levels up to CHEAP_UNTIL use a cheaper palette (plain glass, gray concrete, smooth stone,
# lanterns, glass-pane railings). The premium look (tinted glass, polished deepslate, quartz,
# sea lanterns, Domum Ornamentum lights and railings) starts the level after.
EARLY_GAME_MATERIALS = True
CHEAP_UNTIL = 3


class Style:
    """Neoterra materials by building level (modern architecture ~20 years from now).

    Levels 1-3 use a cheaper palette; level 4+ upgrades glass, trim and lighting and uses
    Domum Ornamentum pieces (see CHEAP_UNTIL).
    """

    def __init__(self, level: int):
        self.level = level
        self.early = EARLY_GAME_MATERIALS and level <= CHEAP_UNTIL
        self.WHITE = "white_concrete"
        self.LIGHTGRAY = "light_gray_concrete"
        self.GLASS = "glass" if self.early else "light_gray_stained_glass"
        self.TRIM = "gray_concrete" if self.early else "polished_deepslate"
        self.WOOD = "stripped_spruce_log[axis=y]"
        self.WOOD_X = "stripped_spruce_log[axis=x]"
        self.WOOD_Z = "stripped_spruce_log[axis=z]"
        self.DECK = "spruce_planks"
        self.SEAT = "spruce_stairs"
        self.LEAVES = "azalea_leaves[distance=1,persistent=true,waterlogged=false]"
        self.railing = "glass_pane" if self.early else do_paperwall("gray_concrete", "glass")
        self.counter = ("smooth_stone_slab[type=top,waterlogged=false]" if self.early
                        else do_slab("white_concrete", "top"))

    def ceiling_light(self, bp, x, y_ceiling, z):
        """Lantern hanging under the slab (L1-2) or a recessed DO light in the slab (L3+)."""
        if self.early:
            bp.set(x, y_ceiling - 1, z, "lantern[hanging=true,waterlogged=false]")
        else:
            put(bp, x, y_ceiling, z, do_light("white_concrete", "sea_lantern"))

    def floor(self, x, z):
        if self.early:
            return "smooth_stone" if (x + z) % 6 == 0 else "polished_andesite"
        return "white_concrete" if x % 6 == 0 or z % 6 == 0 else "light_gray_concrete"


def tree(bp, x, y, z, h=3):
    """Small street / roof-garden tree: timber trunk + leaf crown."""
    leaves = "oak_leaves[distance=1,persistent=true,waterlogged=false]"
    for k in range(h):
        bp.set(x, y + k, z, "stripped_oak_log[axis=y]")
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            for k in (h, h + 1):
                if k == h + 1 and abs(dx) + abs(dz) == 2:
                    continue
                if bp.inside(x + dx, y + k, z + dz):
                    bp.set(x + dx, y + k, z + dz, leaves)
    if bp.inside(x, y + h + 2, z):
        bp.set(x, y + h + 2, z, leaves)


def planter(bp, x, y, z, plant="flowering_azalea"):
    bp.set(x, y, z, "moss_block")
    bp.set(x, y + 1, z, plant)


def street_lamp(bp, x, y, z, h=3):
    for k in range(h):
        bp.set(x, y + k, z, "polished_blackstone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
    bp.set(x, y + h, z, "lantern[hanging=false,waterlogged=false]")


def solar_panels(bp, x1, y, z1, x2, z2):
    bp.fill(x1, y, z1, x2, y, z2, "daylight_detector[inverted=false,power=0]")
