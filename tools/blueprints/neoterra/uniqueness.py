"""
Uniqueness check across the style packs.

For every building/level present in Neoterra, Hearthwood and Cascadia it compares each pair of packs:
  size      identical footprint+height?
  palette   Jaccard overlap of the block types used (ignoring air, substitution, beds, huts, racks)
  shape     3D overlap (IoU) of the solid voxels, aligned on the hut block
and lists the pairs that are too alike (same size, palette overlap > MAXPAL or shape IoU > MAXIOU).

usage: python uniqueness.py [--all]
"""
from __future__ import annotations

import itertools
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from blueprint import load, AIR  # noqa: E402

ROOT = Path(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--root=")), Path(__file__).resolve().parents[3] / "stylepacks"))
PACKS = ("Neoterra", "Hearthwood", "Cascadia")
MAXPAL, MAXIOU = 0.35, 0.55
IGNORE = ("substitution", "blockhut", "rack", "_bed", "ladder", "door", "air", "lantern", "carpet", "torch",
          # blocks MineColonies requires in every version (work blocks), identical by necessity
          "crafting_table", "furnace", "smoker", "barrel", "anvil", "lectern", "bookshelf", "stonecutter", "grindstone",
          "loom", "cartography", "fletching", "smithing", "brewing", "enchanting", "cauldron", "composter", "chest",
          "jukebox", "bell", "beehive", "bee_nest", "target", "hopper", "blast_furnace", "field", "grave", "farmland",
          "water", "lava", "rail", "obsidian", "portal", "scarecrow")


def blocks(bp):
    pal, vox = set(), set()
    ox, oy, oz = bp.primary_offset
    for x, y, z, s in bp.blocks():
        if s == AIR:
            continue
        n = s.split("[")[0].split(":")[-1]
        if y >= 2 and not any(t in n for t in IGNORE):
            pal.add(n)
        if y >= 2 and "substitution" not in n:
            vox.add((x - ox, y - oy, z - oz))
    return pal, vox


def main(show_all=False):
    files = defaultdict(dict)
    for p in PACKS:
        for f in (ROOT / p).rglob("*.blueprint"):
            rel = f.relative_to(ROOT / p).as_posix()
            if re.search(r"\d\.blueprint$", rel):
                files[rel][p] = f
    bad = []
    stats = []
    for rel, by in sorted(files.items()):
        if len(by) < 2:
            continue
        data = {p: load(f) for p, f in by.items()}
        info = {p: blocks(bp) for p, bp in data.items()}
        for a, b in itertools.combinations(sorted(by), 2):
            A, Bp = data[a], data[b]
            same = (A.sx, A.sy, A.sz) == (Bp.sx, Bp.sy, Bp.sz)
            pa, pb = info[a][0], info[b][0]
            pal = len(pa & pb) / max(1, len(pa | pb))
            va, vb = info[a][1], info[b][1]
            iou = len(va & vb) / max(1, len(va | vb))
            stats.append((rel, a, b, same, pal, iou))
            if same or pal > MAXPAL or iou > MAXIOU:
                bad.append((rel, a, b, same, pal, iou))
    for rel, a, b, same, pal, iou in (stats if show_all else bad):
        print(f"{rel:55s} {a[:4]}-{b[:4]}  size {'SAME' if same else 'diff'}  palette {pal:.2f}  shape {iou:.2f}")
    n = len(stats)
    print(f"\n{len(bad)} of {n} pairs too alike  (same size {sum(s[3] for s in stats)}, "
          f"palette>{MAXPAL} {sum(s[4] > MAXPAL for s in stats)}, shape>{MAXIOU} {sum(s[5] > MAXIOU for s in stats)})")
    return bad


if __name__ == "__main__":
    main("--all" in sys.argv)
