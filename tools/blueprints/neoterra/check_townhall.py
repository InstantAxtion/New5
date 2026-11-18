"""Sanity checks for the generated town hall levels (walkability, enchanting, elevator)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import townhall as th  # noqa: E402
from common import parse_state  # noqa: E402

C = th.C


def name(bp, x, y, z):
    return parse_state(bp.get(x, y, z))[0].split(":")[1]


def passable(n):
    return n in ("air", "lantern") or n.endswith(("door",))


def solid(n):
    return n not in ("air", "water") and "door" not in n


def check(level):
    bp = th.build(level)
    problems = []
    # 1. stairs/landings in the core have 2 blocks of headroom
    for x in range(C - 2, C + 3):
        for z in range(C - 2, C + 3):
            if max(abs(x - C), abs(z - C)) != 2:
                continue
            for y in range(1, th.SY - 2):
                n = name(bp, x, y, z)
                if n.endswith("stairs") or (n in ("smooth_stone", "smooth_quartz") and y > 1):
                    for h in (1, 2):
                        if not passable(name(bp, x, y + h, z)) and not name(bp, x, y + h, z).endswith("stairs"):
                            problems.append(f"no headroom above core cell {(x, y, z)}")
    # 2. every exit: opening clear, ground to stand on outside
    exits = th.spiral(th.Blueprint(th.SX, th.SY, th.SZ, "tmp"), th.TOP[level], "stone", "stone_stairs")
    for (cx, cz, wx, wz), f in exits:
        ox, oz = wx + (wx - cx), wz + (wz - cz)
        for y in (f + 1, f + 2):
            for px, pz in ((wx, wz), (ox, oz)):
                if not passable(name(bp, px, y, pz)):
                    problems.append(f"exit at floor {f} blocked at {(px, y, pz)}: {name(bp, px, y, pz)}")
        if not solid(name(bp, ox, f, oz)):
            problems.append(f"exit at floor {f}: nothing to stand on at {(ox, f, oz)}")
    # 3. enchanting table power
    for x, y, z, s in bp.blocks():
        if s.endswith("enchanting_table"):
            shelves = 0
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    if max(abs(dx), abs(dz)) != 2:
                        continue
                    for dy in (0, 1):
                        if name(bp, x + dx, y + dy, z + dz) == "bookshelf":
                            mx, mz = x + (dx > 0) - (dx < 0), z + (dz > 0) - (dz < 0)
                            if name(bp, mx, y + dy, mz) == "air":
                                shelves += 1
            print(f"  L{level}: enchanting table at {(x, y, z)} sees {shelves} bookshelves")
            if shelves < 15:
                problems.append("enchanting table has fewer than 15 bookshelves")
    # 4. elevator is watertight
    if level >= 4:
        tx, tz = th.TUBE
        for y in range(2, 42):
            if name(bp, tx, y, tz) != "water":
                problems.append(f"elevator column broken at y{y}")
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    if (dx, dz) == (0, 0):
                        continue
                    n = name(bp, tx + dx, y, tz + dz)
                    if n in ("air",) or n.endswith(("pane", "paperwall")):
                        problems.append(f"elevator leaks at {(tx + dx, y, tz + dz)}: {n}")
        if name(bp, tx, 1, tz) != "soul_sand":
            problems.append("no soul sand under the elevator")
    # 5. hut block present exactly once
    huts = [p for p, te in bp.tile_entities.items() if str(te.get("id")) == "minecolonies:colonybuilding"]
    if len(huts) != 1 or tuple(bp.primary_offset) != huts[0]:
        problems.append(f"hut block/anchor mismatch: {huts} vs {bp.primary_offset}")
    print(f"L{level}: exits {[(f, (wx, wz)) for (_, _, wx, wz), f in exits]}")
    for p in problems:
        print("  PROBLEM:", p)
    return not problems


if __name__ == "__main__":
    ok = all([check(lvl) for lvl in range(1, 6)])
    sys.exit(0 if ok else 1)
