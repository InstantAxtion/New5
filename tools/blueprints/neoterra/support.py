"""
Support pass – no floating parts.

Finds every group of blocks that is not connected (through any face) to the ground and fixes it:
  * small groups (decor bits, stray blocks) are removed,
  * larger ones (pods, platforms, bridges, canopies) get posts down to the ground or to the
    structure below, in the building's trim material.
If posts would block a walkway (walk-checked), the group is removed instead – unless it holds
anything functional, in which case the posts stay and the group is left as built.

usage: python support.py <dir> [style]
"""
from __future__ import annotations

import itertools
import re
import sys
from collections import deque
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from blueprint import load, AIR  # noqa: E402
from detail import Detailer, nm  # noqa: E402

POST = {"Neoterra": ("white_concrete", "quartz_pillar[axis=y]"),
        "Hearthwood": ("stripped_spruce_log[axis=y]", "stripped_dark_oak_log[axis=y]"),
        "Cascadia": ("dark_oak_log[axis=y]", "dark_oak_log[axis=y]")}
STYLE = "Neoterra"
NEIGH = [d for d in itertools.product((-1, 0, 1), repeat=3) if d != (0, 0, 0)]   # edges and corners count


class Support(Detailer):
    def __init__(self, bp, level, name):
        super().__init__(bp, level, name)
        self.gy = next((p[1] for p, n in self.tags.items() if "groundlevel" in n), 1)

    def components(self):
        bp, gy = self.bp, self.gy
        filled = {(x, y, z) for x, y, z, s in bp.blocks() if s != AIR}
        seen, grounded = set(), set()
        q = deque(p for p in filled if p[1] <= gy)
        seen |= set(q)
        while q:
            x, y, z = q.popleft()
            for d in NEIGH:
                p = (x + d[0], y + d[1], z + d[2])
                if p in filled and p not in seen:
                    seen.add(p)
                    q.append(p)
        grounded = seen
        rest = filled - grounded
        comps = []
        while rest:
            start = rest.pop()
            comp, q = {start}, deque([start])
            while q:
                x, y, z = q.popleft()
                for d in NEIGH:
                    p = (x + d[0], y + d[1], z + d[2])
                    if p in rest:
                        rest.discard(p)
                        comp.add(p)
                        q.append(p)
            comps.append(comp)
        return comps

    def remove(self, comp):
        if any(p in self.protect for p in comp):
            return False
        for x, y, z in comp:
            self.bp.set(x, y, z, AIR)
        return True

    def prop(self, comp):
        bp = self.bp
        post = POST.get(STYLE, POST["Neoterra"])[1 if self.L >= 4 else 0]
        low = min(y for _, y, _ in comp)
        bottom = [(x, z) for x, y, z in comp if y == low]
        xs, zs = [x for x, _ in bottom], [z for _, z in bottom]
        corners = {(min(xs), min(zs)), (max(xs), min(zs)), (min(xs), max(zs)), (max(xs), max(zs))}
        picks = []
        for cx, cz in corners:                      # nearest bottom cell to each footprint corner
            picks.append(min(bottom, key=lambda p: abs(p[0] - cx) + abs(p[1] - cz)))
        if len(bottom) <= 3:
            picks = bottom
        placed = 0
        for x, z in set(picks):
            y = low - 1
            col = []
            while y > 0 and bp.get(x, y, z) == AIR:
                col.append(y)
                y -= 1
            if not col:
                continue
            for yy in col:
                bp.set(x, yy, z, "minecraft:" + post)
            placed += 1
        return placed > 0

    def run(self):
        fixed = []
        for comp in sorted(self.components(), key=len):
            if len(comp) <= 6 and not any(p in self.protect for p in comp):
                if self.guarded(lambda c=comp: self.remove(c)):
                    fixed.append(f"-{len(comp)}")
                continue
            if self.guarded(lambda c=comp: self.prop(c)):
                fixed.append(f"+posts({len(comp)})")
            elif self.guarded(lambda c=comp: self.remove(c)):
                fixed.append(f"-{len(comp)}")
        return fixed


def process(args):
    global STYLE
    path, STYLE = Path(args[0]), args[1]
    m = re.search(r"(\d+)\.blueprint$", path.name)
    if "/mineshafts/" in path.as_posix() or "ship" in path.name or re.match(r"(bunker[a-z]+|skytowerflat|barrackstower)", path.name):
        return f"{path.name}: kept"
    bp = load(path)
    lvl = int(m.group(1)) if m and 1 <= int(m.group(1)) <= 5 else 4
    s = Support(bp, lvl, path.stem)
    fixed = s.run()
    if fixed:
        bp.save(path)
    return f"{path.name}: {' '.join(fixed) or 'ok'}"


def main():
    style = sys.argv[2] if len(sys.argv) > 2 else "Neoterra"
    files = sorted(Path(sys.argv[1]).rglob("*.blueprint"))
    with Pool() as pool:
        for line in pool.imap_unordered(process, [(str(f), style) for f in files], chunksize=2):
            if not line.endswith(("ok", "kept")):
                print(line)


if __name__ == "__main__":
    main()
