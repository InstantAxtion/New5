"""
Domum Ornamentum pass – every pack gets its own set of Domum blocks, more of them at higher levels.

  Hearthwood  L2+ Domum shutters (striped trapdoors) | L3+ timber-framed upper storeys (dark-oak frames, white plaster
              infill, plain and crossed) | L4+ shingle roofs (brown tile; black tile at L5) | L5 frames on every storey
              with brick infill on the ground floor
  Cascadia    L2+ squared timber pillars on the corner logs | L3+ log-cabin frames (horizontal) on upper storeys |
              L4+ cedar shingle roofs (mossy shingles mixed in at L5) | L5 frames on every storey
  Neoterra    L2+ framed lights | L3+ quartz square pillars on the corners | L4+ every light framed | L5 framed light strips

Only blocks facing the outside are changed (roofs, walls, posts, shutters); huts, racks, beds, work blocks and anything
with block data are left alone. Level 1-3 buildings that stop at level 3 use the level 1 / 3 / 5 rules.

usage: python domumize.py <pack dir> <style>
"""
from __future__ import annotations

import re
import sys
from collections import deque
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from blueprint import load, parse_state, AIR  # noqa: E402
from common import do_te, K_MAIN, K_SECOND  # noqa: E402

K_CLAY = "minecraft:block/clay"
H4 = ((1, 0, "east"), (-1, 0, "west"), (0, 1, "south"), (0, -1, "north"))
SKIP_DIRS = ("/mineshafts/", "/supplies/", "/fields/")
MAX3 = ("tavern", "gatehouse", "watchtower")

PLASTER = {"white_terracotta", "light_gray_terracotta", "pink_terracotta", "yellow_terracotta", "light_blue_terracotta",
           "white_stained_glass"}
CASC_WALL = {"mangrove_planks", "spruce_planks", "stripped_spruce_wood", "stripped_mangrove_wood"}
CASC_POST = {"spruce_log", "mangrove_log", "stripped_spruce_log", "stripped_mangrove_log", "dark_oak_log"}
NEO_POST = {"gray_concrete", "white_concrete", "smooth_stone"}
NEO_FLOOR = {"polished_andesite", "smooth_stone", "smooth_quartz", "polished_diorite"}
NEO_PARAPET = {"light_gray_concrete", "white_concrete", "gray_concrete", "smooth_stone"}
NEO_ROOFDECK = {"polished_andesite", "smooth_stone", "smooth_quartz", "light_gray_concrete", "polished_diorite"}


def name(s):
    return s.split("[")[0].split(":")[-1]


def tier(path: Path):
    m = re.search(r"(\d)\.blueprint$", path.name)
    if not m:
        return 3
    L = int(m.group(1))
    if any(path.name.startswith(k) for k in MAX3):
        return {1: 1, 2: 3, 3: 5}.get(L, L)
    return max(1, min(5, L))


def outside_air(bp):
    out = set()
    q = deque()
    sx, sy, sz = bp.sx, bp.sy, bp.sz
    for x in range(sx):
        for z in range(sz):
            for y in range(sy):
                if (x in (0, sx - 1) or z in (0, sz - 1) or y == sy - 1) and bp.get(x, y, z) == AIR:
                    out.add((x, y, z))
                    q.append((x, y, z))
    while q:
        x, y, z = q.popleft()
        for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            n = (x + dx, y + dy, z + dz)
            if n in out or not bp.inside(*n) or bp.get(*n) != AIR:
                continue
            out.add(n)
            q.append(n)
    return out


def facing_out(out, x, y, z):
    for dx, dz, f in H4:
        if (x + dx, y, z + dz) in out:
            return f
    return None


def is_roof_stair(bp, out, x, y, z, s):
    if "_stairs" not in s or (x, y + 1, z) not in out:
        return False
    for dx, dz, _ in H4:
        for dy in (-1, 1):
            if "_stairs" in bp.get(x + dx, y + dy, z + dz) or "_slab" in bp.get(x + dx, y + dy, z + dz):
                return True
    return False


def process(args):
    path, style = Path(args[0]), args[1]
    p = path.as_posix()
    if any(k in p for k in SKIP_DIRS):
        return None
    bp = load(path)
    t = tier(path)
    if t < 2:
        return None
    out = outside_air(bp)
    changed = 0
    te_pos = set(bp.tile_entities)

    def put(x, y, z, state, tex):
        nonlocal changed
        bp.set(x, y, z, state, do_te(tex))
        changed += 1

    cells = [(x, y, z, s) for x, y, z, s in bp.blocks() if s != AIR and (x, y, z) not in te_pos and y >= 2]
    for x, y, z, s in cells:
        n = name(s)
        _, props = parse_state(s)
        if style == "Hearthwood":
            if t >= 2 and n.endswith("_trapdoor") and props.get("open") == "true" and facing_out(out, x, y, z) is not None:
                put(x, y, z, f"domum_ornamentum:vanilla_trapdoors_compat[facing={props.get('facing', 'north')},half={props.get('half', 'bottom')},"
                             f"open=true,powered=false,type=vertically_striped,waterlogged=false]", {K_MAIN: "minecraft:dark_oak_planks"})
            elif t >= 4 and is_roof_stair(bp, out, x, y, z, s):
                put(x, y, z, f"domum_ornamentum:shingle[facing={props.get('facing', 'north')},half={props.get('half', 'bottom')},"
                             f"shape={props.get('shape', 'straight')},waterlogged=false]",
                    {K_CLAY: "domum_ornamentum:black_brick_extra" if t >= 5 else "domum_ornamentum:brown_brick_extra",
                     K_MAIN: "minecraft:dark_oak_planks"})
            elif n in PLASTER and (t >= 5 or (t >= 3 and y >= 6)):
                f = facing_out(out, x, y, z)
                if f:
                    kind = "double_crossed" if (x + z + y) % 7 == 0 else ("one_crossed_lr" if (x + z) % 5 == 1 else "plain")
                    infill = "domum_ornamentum:brick_extra" if (t >= 5 and y < 6) else "domum_ornamentum:white_paper_extra"
                    put(x, y, z, f"domum_ornamentum:{kind}[facing={f}]",
                        {K_MAIN: "minecraft:dark_oak_planks", K_SECOND: infill})
        elif style == "Cascadia":
            if t >= 2 and n in CASC_POST and props.get("axis", "y") == "y":
                f = facing_out(out, x, y, z)
                if f:
                    below = name(bp.get(x, y - 1, z)) in CASC_POST
                    above = name(bp.get(x, y + 1, z)) in CASC_POST
                    col = "pillar_column" if below and above else ("pillar_base" if above else ("pillar_capital" if below else "full_pillar"))
                    put(x, y, z, f"domum_ornamentum:squarepillar[column={col}]", {K_MAIN: "minecraft:stripped_spruce_log"})
            elif t >= 4 and is_roof_stair(bp, out, x, y, z, s):
                clay = "domum_ornamentum:mossy_cobblestone_extra" if (t >= 5 and (x * 3 + z) % 5 == 0) else "minecraft:spruce_planks"
                put(x, y, z, f"domum_ornamentum:shingle[facing={props.get('facing', 'north')},half={props.get('half', 'bottom')},"
                             f"shape={props.get('shape', 'straight')},waterlogged=false]",
                    {K_CLAY: clay, K_MAIN: "minecraft:spruce_planks"})
            elif n in CASC_WALL and (t >= 5 or (t >= 3 and y >= 6)):
                f = facing_out(out, x, y, z)
                if f:
                    put(x, y, z, f"domum_ornamentum:horizontal_plain[facing={f}]",
                        {K_MAIN: "minecraft:spruce_planks", K_SECOND: "minecraft:stripped_spruce_log"})
        else:  # Neoterra
            above_in = bp.get(x, y + 1, z) == AIR and (x, y + 1, z) not in out
            if t >= 4 and is_roof_stair(bp, out, x, y, z, s):                     # standing-seam metal roof
                put(x, y, z, f"domum_ornamentum:shingle[facing={props.get('facing', 'north')},half={props.get('half', 'bottom')},"
                             f"shape={props.get('shape', 'straight')},waterlogged=false]",
                    {K_CLAY: "minecraft:iron_block" if t >= 5 else "minecraft:light_gray_concrete", K_MAIN: "minecraft:white_concrete"})
                continue
            if t >= 3 and n in NEO_FLOOR and above_in and y >= 2:                   # framed floor tiles
                infill = ("minecraft:smooth_quartz" if (x + z) % 2 else "minecraft:white_concrete") if t >= 5 else "minecraft:smooth_quartz"
                put(x, y, z, "domum_ornamentum:framed[facing=up]", {K_MAIN: "minecraft:light_gray_concrete", K_SECOND: infill})
                continue
            if t >= 3 and n in NEO_PARAPET and (x, y + 1, z) in out and y >= 4 and facing_out(out, x, y, z):
                put(x, y, z, "domum_ornamentum:side_framed[facing=up]",
                    {K_MAIN: "minecraft:quartz_block", K_SECOND: "minecraft:light_gray_concrete"})
                continue
            if "_stairs" in n and not is_roof_stair(bp, out, x, y, z, s) and t >= 3 and (x, y, z) not in out and above_in:
                put(x, y, z, f"domum_ornamentum:vanilla_stairs_compat[facing={props.get('facing', 'north')},half={props.get('half', 'bottom')},"
                             f"shape={props.get('shape', 'straight')},waterlogged=false]", {K_MAIN: "minecraft:smooth_quartz"})
                continue
            if "_slab" in n and props.get("type") == "top" and t >= 2 and above_in and facing_out(out, x, y, z) is None:
                put(x, y, z, "domum_ornamentum:vanilla_slab_compat[type=top,waterlogged=false]", {K_MAIN: "minecraft:smooth_quartz"})
                continue
            if n == "lantern" and t >= 2 and props.get("hanging") == "true":
                if t >= 4 or (x + z) % 2 == 0:
                    if bp.get(x, y - 1, z) == AIR and bp.get(x, y - 2, z) == AIR and bp.get(x, y + 1, z) != AIR:
                        put(x, y, z, "domum_ornamentum:fancy_light", {K_MAIN: "minecraft:quartz_block",
                                                                       "minecraft:block/glowstone": "minecraft:sea_lantern"})
            elif n == "sea_lantern" and t >= 5:
                put(x, y, z, "domum_ornamentum:center_light", {K_MAIN: "minecraft:white_concrete",
                                                               "minecraft:block/glowstone": "minecraft:sea_lantern"})
            elif t >= 3 and n in NEO_POST:
                outs = [f for dx, dz, f in H4 if (x + dx, y, z + dz) in out]
                corner = len(outs) >= 2 and not ({"east", "west"} <= set(outs) or {"north", "south"} <= set(outs))
                if corner:
                    below = name(bp.get(x, y - 1, z)) in NEO_POST
                    above = name(bp.get(x, y + 1, z)) in NEO_POST
                    col = "pillar_column" if below and above else ("pillar_base" if above else ("pillar_capital" if below else "full_pillar"))
                    put(x, y, z, f"domum_ornamentum:squarepillar[column={col}]",
                        {K_MAIN: "minecraft:quartz_block" if t >= 5 else "minecraft:smooth_quartz"})
    if style == "Neoterra" and t >= 4:                                         # waffle-panel decking on flat roofs
        for x, y, z, s in [(x, y, z, s) for x, y, z, s in bp.blocks() if s == AIR and y >= 6]:
            if (x, y, z) not in out:
                continue
            below = bp.get(x, y - 1, z)
            if name(below) in NEO_ROOFDECK and (x, y - 1, z) not in te_pos and bp.get(x, y - 2, z) == AIR \
                    and (x, y - 2, z) not in out:
                put(x, y, z, "domum_ornamentum:panel[facing=north,half=bottom,open=false,type=waffle,waterlogged=false]",
                    {K_MAIN: "minecraft:gray_concrete"})
    if changed:
        bp.save(path)
    return changed


def main():
    root, style = Path(sys.argv[1]), sys.argv[2]
    jobs = [(str(f), style) for f in sorted(root.rglob("*.blueprint"))]
    total = files = 0
    with Pool() as pool:
        for n in pool.imap_unordered(process, jobs, chunksize=4):
            if n:
                total += n
                files += 1
    print(f"{style}: Domum blocks placed: {total} in {files} blueprints")


if __name__ == "__main__":
    main()
