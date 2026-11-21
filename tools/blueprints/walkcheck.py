"""
Approximate walkability check for a blueprint (what a citizen or player can reach on foot).

Starts on every ground cell at the edge of the blueprint and flood-fills positions a walker
can stand in (2 free blocks, something solid underneath), allowing 1-block step-ups (stairs,
slabs, jumps), drops of up to 3 blocks, ladders and doors. Then reports beds, the hut block,
racks and work blocks that have no reachable standing spot next to them.

usage: python walkcheck.py file.blueprint [...]
"""
from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from blueprint import load, parse_state  # noqa: E402

PASSABLE_KEYS = ("air", "door", "ladder", "lantern", "carpet", "short_grass", "rail", "torch",
                 "end_rod", "chain", "pressure_plate", "button", "lever", "sign", "flower", "water")
NOT_STANDABLE = ("fence", "_wall", "pane", "paperwall", "bars", "leaves", "water", "door",
                 "ladder", "lantern", "carpet", "short_grass", "chain", "end_rod", "lightning_rod",
                 "flowering_azalea", "azalea", "bed")
TARGET_KEYS = ("bed", "blockhut", "rack", "crafting_table", "furnace", "smoker", "barrel",
               "enchanting_table", "anvil", "smithing_table", "stonecutter", "lectern", "ender_chest",
               "cartography_table", "loom", "grindstone", "brewing_stand", "architectscutter")


def short(s):
    return parse_state(s)[0].split(":")[1]


def analyse(bp, return_seen=False):
    def name(x, y, z):
        return short(bp.get(x, y, z)) if bp.inside(x, y, z) else "air"

    def passable(x, y, z):
        n = name(x, y, z)
        if n.endswith("_wall") or n.endswith("trapdoor") or n == "sea_lantern":
            return False
        return n == "air" or any(k in n for k in PASSABLE_KEYS if k != "air")

    def standable(x, y, z):
        n = name(x, y - 1, z)
        return y - 1 >= 0 and n != "air" and (n == "sea_lantern" or not any(k in n for k in NOT_STANDABLE))

    def ok(x, y, z):
        if not (bp.inside(x, y, z) and y + 1 < bp.sy):
            return False
        if not (passable(x, y, z) and passable(x, y + 1, z)):
            return False
        return standable(x, y, z) or "ladder" in name(x, y, z) or "water" in name(x, y, z)

    start = []
    for x in range(bp.sx):
        for z in range(bp.sz):
            if x in (0, bp.sx - 1) or z in (0, bp.sz - 1):
                for y in range(1, bp.sy - 1):           # lowest open spot = ground level
                    if ok(x, y, z):
                        start.append((x, y, z))
                        break
    seen = set(start)
    q = deque(start)
    while q:
        x, y, z = q.popleft()
        here = name(x, y, z)
        nexts = []
        if "ladder" in here or "water" in here:
            nexts += [(x, y + 1, z), (x, y - 1, z)]
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, nz = x + dx, z + dz
            for dy in (0, 1, -1, -2, -3):
                if dy == 1 and not passable(x, y + 2, z):
                    continue                       # no room to jump up
                ny = y + dy
                if ok(nx, ny, nz) and (dy >= 0 or all(passable(nx, ny + k, nz) for k in range(2, 2 - dy))):
                    nexts.append((nx, ny, nz))
                    break
        if "ladder" in name(x, y - 1, z):
            nexts.append((x, y - 1, z))
        for p in nexts:
            if p not in seen and ok(*p):
                seen.add(p)
                q.append(p)

    problems = []
    for x, y, z, s in bp.blocks():
        n = short(s)
        if not any(k in n for k in TARGET_KEYS) or "bedrock" in n:
            continue
        if "rack" in n and "blockhut" not in n:
            pass
        def reachable(px, py, pz):
            return any((px + dx, py + dy, pz + dz) in seen
                       for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)) for dy in (0, -1, -2, 1))
        reach = reachable(x, y, z)
        if not reach and n.endswith("_bed"):           # a bed only needs one reachable half
            facing = parse_state(s)[1].get("facing", "north")
            fdx, fdz = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}[facing]
            sign = 1 if "part=foot" in s else -1
            reach = reachable(x + sign * fdx, y, z + sign * fdz)
        if not reach:
            problems.append(f"{n} at {(x, y, z)} not reachable")
    beds = sum(1 for *_, s in bp.blocks() if short(s).endswith("_bed") and "part=head" in s)
    if return_seen:
        return beds, problems, seen
    return beds, problems


if __name__ == "__main__":
    bad = 0
    for f in sys.argv[1:]:
        beds, problems = analyse(load(f))
        print(f"{Path(f).name}: {beds} beds, {len(problems)} unreachable")
        for p in problems[:8]:
            print("   ", p)
        bad += len(problems)
    sys.exit(1 if bad else 0)
