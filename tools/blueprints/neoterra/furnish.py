"""
Furnishing pass: every pack furnishes its interiors with its own furniture set, more at higher levels.

  Neoterra    quartz sofas, counters with glass display cases, potted bamboo, cyan / grey rugs
  Hearthwood  bookcases, shelves with flower pots and candles, oak benches, dressers, orange / white rugs
  Cascadia    log benches, stump stools, firewood stacks, plank tables with lanterns, river-rock hearths, brown / green rugs

Furniture goes on free floor spots against interior walls (about 15 % of them at level 1 up to 55 % at level 5) and rugs
in the middle of larger rooms. Doors, ladders, stairs, huts, beds, racks and work blocks keep a clear ring around them,
and every building is walk-checked afterwards; if anything became unreachable, furniture is taken out again until it
is not.

usage: python furnish.py <pack dir> <style>
"""
from __future__ import annotations

import hashlib
import re
import sys
from collections import deque
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from blueprint import load, AIR  # noqa: E402
import walkcheck  # noqa: E402

SKIP_DIRS = ("/mineshafts/", "/supplies/", "/fields/", "/walls/", "/infrastructure/", "/parks/", "/wonders/")
MAX3 = ("tavern", "gatehouse", "watchtower")
KEEP_CLEAR = ("door", "ladder", "stairs", "blockhut", "rack", "_bed", "furnace", "smoker", "crafting_table", "barrel",
              "anvil", "lectern", "bookshelf", "stonecutter", "grindstone", "loom", "cartography", "fletching",
              "smithing", "brewing", "enchanting", "cauldron", "composter", "chest", "bell", "beehive", "target",
              "hopper", "scarecrow", "field", "grave", "jukebox", "trapdoor", "fence_gate", "substitution",
              "portal", "obsidian", "water", "farmland", "rail", "architectscutter")
H4 = ((1, 0, "east"), (-1, 0, "west"), (0, 1, "south"), (0, -1, "north"))
DENSITY = {1: 0.15, 2: 0.25, 3: 0.35, 4: 0.45, 5: 0.55}

# pieces: list of (dy, block) – "{w}" is replaced by the direction of the wall behind the spot
PIECES = {
    "Neoterra": [
        [(0, "smooth_quartz_stairs[facing={w},half=bottom,shape=straight,waterlogged=false]")],                  # sofa
        [(0, "smooth_quartz_stairs[facing={w},half=bottom,shape=straight,waterlogged=false]")],
        [(0, "smooth_quartz"), (1, "light_blue_stained_glass")],                                                  # display case
        [(0, "smooth_quartz_slab[type=top,waterlogged=false]")],                                                  # counter
        [(0, "potted_bamboo")],
    ],
    "Hearthwood": [
        [(0, "chiseled_bookshelf[facing={o},slot_0_occupied=false,slot_1_occupied=false,slot_2_occupied=false,"
             "slot_3_occupied=false,slot_4_occupied=false,slot_5_occupied=false]"),
         (1, "chiseled_bookshelf[facing={o},slot_0_occupied=false,slot_1_occupied=false,slot_2_occupied=false,"
             "slot_3_occupied=false,slot_4_occupied=false,slot_5_occupied=false]")],                              # bookcase
        [(0, "dark_oak_slab[type=top,waterlogged=false]"), (1, "potted_red_tulip")],                              # shelf + pot
        [(0, "oak_stairs[facing={w},half=bottom,shape=straight,waterlogged=false]")],                             # bench
        [(0, "dark_oak_planks"), (1, "candle[candles=3,lit=false,waterlogged=false]")],                           # dresser
        [(0, "dark_oak_slab[type=top,waterlogged=false]"), (1, "potted_azure_bluet")],
    ],
    "Cascadia": [
        [(0, "stripped_spruce_log[axis={a}]")],                                                                   # log bench
        [(0, "spruce_log[axis=y]")],                                                                              # stump stool
        [(0, "spruce_log[axis={a}]"), (1, "spruce_log[axis={a}]")],                                               # firewood
        [(0, "spruce_fence"), (1, "lantern[hanging=false,waterlogged=false]")],                                   # plank table
        [(0, "mossy_cobblestone"), (1, "cobblestone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")],  # hearth
    ],
}
RUGS = {"Neoterra": ("cyan_carpet", "light_gray_carpet"), "Hearthwood": ("orange_carpet", "white_carpet"),
        "Cascadia": ("brown_carpet", "green_carpet")}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}


def h(*a):
    return int.from_bytes(hashlib.md5(repr(a).encode()).digest()[:4], "little")


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
    for x in range(bp.sx):
        for z in range(bp.sz):
            for y in range(bp.sy):
                if (x in (0, bp.sx - 1) or z in (0, bp.sz - 1) or y == bp.sy - 1) and bp.get(x, y, z) == AIR:
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


def process(args):
    path, style = Path(args[0]), args[1]
    if any(k in path.as_posix() for k in SKIP_DIRS):
        return None
    bp = load(path)
    if not any("blockhut" in bp.get(*p) for p in bp.tile_entities):
        return None
    t = tier(path)
    out = outside_air(bp)
    before = len(walkcheck.analyse(bp)[1])
    clear = set()
    for x, y, z, s in bp.blocks():
        if s != AIR and any(k in name(s) for k in KEEP_CLEAR):
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        clear.add((x + dx, y + dy, z + dz))
    wall_spots, open_spots = [], []
    for x, y, z, s in bp.blocks():
        if s != AIR or (x, y, z) in out or (x, y, z) in clear:
            continue
        if bp.get(x, y + 1, z) != AIR or bp.get(x, y + 2, z) != AIR:
            continue
        below = bp.get(x, y - 1, z)
        if below == AIR or any(k in name(below) for k in ("carpet", "slab", "stairs", "fence", "pane", "glass")):
            continue
        walls = [f for dx, dz, f in H4 if bp.get(x + dx, y, z + dz) != AIR and (x + dx, y, z + dz) not in out
                 and "door" not in bp.get(x + dx, y, z + dz) and "glass" not in name(bp.get(x + dx, y, z + dz))]
        if len(walls) == 1:
            wall_spots.append((x, y, z, walls[0]))
        elif not walls and all(bp.get(x + dx, y, z + dz) == AIR for dx, dz, _ in H4):
            open_spots.append((x, y, z))
    wall_spots.sort(key=lambda c: h(path.name, c))
    pieces = PIECES[style]
    n = int(len(wall_spots) * DENSITY[t])
    placed = []
    used = set()
    for (x, y, z, w) in wall_spots:
        if len(placed) >= n:
            break
        if any((x + dx, y, z + dz) in used for dx in (-1, 0, 1) for dz in (-1, 0, 1) if (dx, dz) != (0, 0)) and h(x, z) % 3:
            continue
        piece = pieces[h(path.name, x, y, z) % len(pieces)]
        if any(bp.get(x, y + dy, z) != AIR for dy, _ in piece):
            continue
        axis = "z" if w in ("east", "west") else "x"
        cells = []
        for dy, st in piece:
            cells.append((x, y + dy, z, bp.get(x, y + dy, z)))
            bp.set(x, y + dy, z, "minecraft:" + st.format(w=w, o=OPP[w], a=axis))
        placed.append(cells)
        used.add((x, y, z))
    # rugs in the middle of bigger rooms
    rugs = []
    if t >= 2:
        rug = RUGS[style]
        for (x, y, z) in open_spots:
            if (x + z) % 2 and h(path.name, "rug", x, z) % 3 == 0:
                continue
            if all(bp.get(x + dx, y, z + dz) == AIR and (x + dx, y, z + dz) not in out
                   for dx in (-2, -1, 0, 1, 2) for dz in (-2, -1, 0, 1, 2)):
                rugs.append((x, y, z))
        for (x, y, z) in rugs:
            bp.set(x, y, z, "minecraft:" + rug[(x // 2 + z // 2) % 2])
    # walk-check; take furniture back out until nothing new is unreachable
    while placed and len(walkcheck.analyse(bp)[1]) > before:
        drop = placed[len(placed) // 2:]
        placed = placed[:len(placed) // 2]
        for cells in drop:
            for x, y, z, old in cells:
                bp.set(x, y, z, old)
    if len(walkcheck.analyse(bp)[1]) > before:
        return None                                             # leave the file untouched
    if placed or rugs:
        bp.save(path)
    return len(placed), len(rugs)


def main():
    root, style = Path(sys.argv[1]), sys.argv[2]
    jobs = [(str(f), style) for f in sorted(root.rglob("*.blueprint"))]
    pieces = rugs = files = 0
    with Pool() as pool:
        for r in pool.imap_unordered(process, jobs, chunksize=2):
            if r:
                files += 1
                pieces += r[0]
                rugs += r[1]
    print(f"{style}: {pieces} pieces of furniture and {rugs} rug tiles in {files} buildings")


if __name__ == "__main__":
    main()
