"""
Write the hand-made designs into a style pack (replacing the generated huts of the same path).

usage: python handmade.py <pack dir> <Neoterra|Hearthwood|Cascadia>
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hm  # noqa: E402


def main():
    root, pack = Path(sys.argv[1]), sys.argv[2]
    designs = hm.load_designs()
    n = 0
    for base, fn in sorted(designs.items()):
        for rel in hm.rels_for(base):
            bp = fn(pack, rel, hm.REQ[rel]["level"]).finish()
            dst = root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            bp.save(dst)
            n += 1
    print(f"{pack}: {n} hand-made hut levels ({len(designs)} types)")


if __name__ == "__main__":
    main()
