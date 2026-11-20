"""
Replace every Domum Ornamentum block in a pack with its closest vanilla block (the user wants vanilla blocks only).

Material comes from the block's textureData (shingle: roof material, frames: infill, pillars / panels: main), shape
from its block state (stairs keep facing/half/shape, trapdoors keep facing/half/open). The architect's cutter is kept
(the builder hut requires it). Pane connections are recomputed afterwards.

usage: python vanillaize.py <pack dir>
"""
from __future__ import annotations

import gzip
import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from blueprint import load, parse_state, format_state  # noqa: E402
from common import connect_panes  # noqa: E402

ROOF = {"black_brick_extra": "deepslate_tile", "brown_brick_extra": "mud_brick", "iron_block": "polished_andesite",
        "light_gray_concrete": "andesite", "mossy_cobblestone_extra": "mossy_cobblestone", "spruce_planks": "spruce",
        "dark_oak_planks": "dark_oak", "white_concrete": "smooth_quartz", "smooth_quartz": "smooth_quartz",
        "quartz_block": "quartz", "oak_planks": "oak", "stone_bricks": "stone_brick", "bricks": "brick"}
INFILL = {"white_paper_extra": "calcite", "brick_extra": "bricks", "paper_extra": "smooth_sandstone",
          "stripped_spruce_log": "stripped_spruce_log", "cobblestone_extra": "cobblestone",
          "mossy_cobblestone_extra": "mossy_cobblestone", "black_brick_extra": "deepslate_bricks",
          "brown_brick_extra": "mud_bricks"}
FRAMES = ("plain", "framed", "side_framed", "horizontal_plain", "one_crossed_lr", "one_crossed_rl", "double_crossed",
          "up_gated", "down_gated", "horizontal_crossed", "vertical_crossed")


def tex(te, key):
    td = te.get("textureData", {}) if te is not None else {}
    v = td.get(f"minecraft:block/{key}")
    return str(v).split(":")[-1] if v is not None else None


def full(m):
    m = INFILL.get(m, m)
    if m.endswith("_log") or m.endswith("_stem"):
        return f"{m}[axis=y]"
    return m


def convert(name, props, te):
    main = tex(te, "oak_planks") or "oak_planks"
    if name == "shingle" or name == "shingle_slab":
        roof = ROOF.get(tex(te, "clay") or main, "deepslate_tile")
        if name == "shingle_slab":
            return f"{roof}_slab[type=bottom,waterlogged=false]"
        return format_state(f"minecraft:{roof}_stairs", {"facing": props.get("facing", "north"),
                                                          "half": props.get("half", "bottom"),
                                                          "shape": props.get("shape", "straight"),
                                                          "waterlogged": "false"})
    if name in FRAMES:
        infill = tex(te, "dark_oak_planks") or main
        if name == "horizontal_plain" and infill.endswith("_log"):
            axis = "x" if props.get("facing", "north") in ("north", "south", "up", "down") else "z"
            return f"{infill}[axis={axis}]"
        return full(infill)
    if name == "squarepillar" or name == "blockpillar":
        if main in ("quartz_block", "smooth_quartz"):
            return "quartz_pillar[axis=y]"
        return full(main)
    if name.endswith("_light"):
        return "sea_lantern"
    if name == "panel":
        return format_state("minecraft:iron_trapdoor", {k: props[k] for k in ("facing", "half", "open") if k in props}
                            | {"powered": "false", "waterlogged": "false"})
    if name == "vanilla_trapdoors_compat":
        wood = main.replace("_planks", "") if main.endswith("_planks") else "oak"
        return format_state(f"minecraft:{wood}_trapdoor", {k: props[k] for k in ("facing", "half", "open") if k in props}
                            | {"powered": "false", "waterlogged": "false"})
    if name == "vanilla_stairs_compat":
        m = ROOF.get(main, main.replace("_planks", ""))
        return format_state(f"minecraft:{m}_stairs", {"facing": props.get("facing", "north"),
                                                      "half": props.get("half", "bottom"),
                                                      "shape": props.get("shape", "straight"), "waterlogged": "false"})
    if name == "vanilla_slab_compat":
        m = ROOF.get(main, main.replace("_planks", ""))
        if m == "white_concrete":
            m = "smooth_quartz"
        return f"minecraft:{m}_slab[type={props.get('type', 'bottom')},waterlogged=false]"
    if name == "blockpaperwall":
        return "minecraft:glass_pane[east=false,north=false,south=false,waterlogged=false,west=false]"
    if name in ("fancy_door",):
        return format_state("minecraft:dark_oak_door", {k: props[k] for k in ("facing", "half", "hinge", "open")
                                                        if k in props} | {"powered": "false"})
    if name in ("fancy_trapdoor",):
        return format_state("minecraft:dark_oak_trapdoor", {k: props[k] for k in ("facing", "half", "open")
                                                            if k in props} | {"powered": "false", "waterlogged": "false"})
    if name in ("vanilla_wall_compat",):
        return "minecraft:cobblestone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]"
    if name in ("vanilla_fence_compat",):
        return "minecraft:oak_fence[east=false,north=false,south=false,waterlogged=false,west=false]"
    raise KeyError(name)


def process(path):
    path = Path(path)
    if b"domum_ornamentum" not in gzip.open(path).read():
        return 0
    bp = load(path)
    n = 0
    for x, y, z, s in list(bp.blocks()):
        full_name, props = parse_state(s)
        if not full_name.startswith("domum_ornamentum:") or full_name.endswith("architectscutter"):
            continue
        te = bp.tile_entities.get((x, y, z))
        new = convert(full_name.split(":")[1], props, te)
        bp.set(x, y, z, new if ":" in new else "minecraft:" + new)
        n += 1
    if n:
        connect_panes(bp)
        bp.save(path)
    return n


def main():
    root = Path(sys.argv[1])
    files = sorted(str(f) for f in root.rglob("*.blueprint"))
    with Pool() as pool:
        counts = pool.map(process, files, chunksize=4)
    print(f"{root.name}: {sum(counts)} Domum blocks replaced with vanilla in {sum(1 for c in counts if c)} files")


if __name__ == "__main__":
    main()
