"""
Find rough interiors in built blueprints: rooms with little furniture, and floors that repeat another floor exactly.

usage: python roomcheck.py <blueprint files or dirs> [--min-area=16] [--density=0.15] [--csv=out.csv]

A room = a connected area of indoor walkable cells on one floor (air at y and y+1, solid below, a roof somewhere
above); doors, walls and furniture taller than one block bound it. Furniture = cells inside the room at y..y+2
(plus wall-mounted pieces on its walls) holding a furnishing block (not a plain building block).
"""
from __future__ import annotations

import sys
from collections import Counter, deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))
sys.path.insert(0, str(HERE.parent))
from blueprint import AIR, load  # noqa: E402

FURN = ("stairs", "slab", "fence", "carpet", "lantern", "torch", "bed", "chest", "barrel", "table", "flower_pot",
        "potted", "candle", "banner", "sign", "anvil", "cauldron", "lectern", "loom", "smoker", "furnace",
        "bookshelf", "crafting", "composter", "brewing", "grindstone", "bell", "campfire", "rack", "pressure_plate",
        "trapdoor", "button", "lamp", "end_rod", "chain", "head", "skull", "hay", "cake", "pickle", "cutter",
        "stonecutter", "smithing", "fletching", "cartography", "jukebox", "note_block", "beehive", "barrel",
        "armor", "pane", "bars", "lightning_rod", "decorated_pot", "flower", "leaves", "azalea", "fern", "sapling",
        "hut", "dripleaf", "glow_lichen", "scaffolding", "ladder", "wall_", "_wall", "enchanting", "respawn",
        "lodestone", "target", "dispenser", "dropper", "hopper", "observer", "kelp", "sea_pickle", "conduit",
        "grave", "door", "vine", "moss_carpet", "bamboo", "candle_cake", "shulker", "ender_chest", "sea_lantern",
        "froglight", "shroomlight", "glowstone", "redstone_lamp", "beacon", "melon", "pumpkin", "dried_kelp")


def is_furn(st):
    if st == AIR or "substitution" in st:
        return False
    n = st.split("[")[0].split(":")[-1]
    return any(k in n for k in FURN)


def blocks_walk(st):
    n = st.split("[")[0].split(":")[-1]
    if n in ("flowering_azalea", "azalea"):
        return True
    return st != AIR and not any(k in n for k in ("carpet", "pressure_plate", "torch", "rail", "button", "_sign",
                                                    "flower", "sapling", "fern", "short_grass", "snow"))


def ground_y(bp):
    try:
        import plotmax
        te = plotmax.hut_info(bp)
        if te is not None:
            return plotmax.ground_y(bp, te)
    except Exception:
        pass
    return 1


def rooms(bp):
    gy = ground_y(bp)
    g = bp.grid
    sx, sy, sz = bp.sx, bp.sy, bp.sz

    def get(x, y, z):
        if 0 <= x < sx and 0 <= y < sy and 0 <= z < sz:
            return g[y][z][x]
        return AIR

    def roofed(x, y, z):
        return any(get(x, yy, z) != AIR for yy in range(y + 2, min(sy, y + 14)))

    out = []
    seen = set()
    for y in range(1, sy - 2):
        if y < gy - 40:
            continue
        for z in range(sz):
            for x in range(sx):
                if (x, y, z) in seen:
                    continue
                c = get(x, y, z)
                if blocks_walk(c) or blocks_walk(get(x, y + 1, z)) or get(x, y - 1, z) == AIR:
                    continue
                if "door" in c or not roofed(x, y, z):
                    continue
                cells = []
                q = deque([(x, z)])
                seen.add((x, y, z))
                while q:
                    cx, cz = q.popleft()
                    cells.append((cx, cz))
                    for nx, nz in ((cx + 1, cz), (cx - 1, cz), (cx, cz + 1), (cx, cz - 1)):
                        if (nx, y, nz) in seen or not (0 <= nx < sx and 0 <= nz < sz):
                            continue
                        n = get(nx, y, nz)
                        if blocks_walk(n) or blocks_walk(get(nx, y + 1, nz)) or get(nx, y - 1, nz) == AIR:
                            continue
                        if "door" in n or not roofed(nx, y, nz):
                            continue
                        seen.add((nx, y, nz))
                        q.append((nx, nz))
                if len(cells) < 6:
                    continue
                cs = set(cells)
                furn = set()
                for cx, cz in cells:
                    for yy in (y - 1, y, y + 1, y + 2):
                        if yy >= y and is_furn(get(cx, yy, cz)):
                            furn.add((cx, yy, cz))
                    for nx, nz in ((cx + 1, cz), (cx - 1, cz), (cx, cz + 1), (cx, cz - 1)):
                        if (nx, nz) in cs:
                            continue
                        for yy in (y, y + 1, y + 2):
                            st = get(nx, yy, nz)
                            if is_furn(st) and "pane" not in st and "door" not in st:
                                furn.add((nx, yy, nz))
                    # ceiling lights
                    for yy in range(y + 2, min(sy, y + 6)):
                        st = get(cx, yy, cz)
                        if st != AIR:
                            if is_furn(st):
                                furn.add((cx, yy, cz))
                            break
                xs = [c[0] for c in cells]
                zs = [c[1] for c in cells]
                sig = Counter(get(fx, fy, fz).split("[")[0] for fx, fy, fz in furn)
                shape = frozenset((cx - min(xs), cz - min(zs)) for cx, cz in cells)
                out.append(dict(y=y, x1=min(xs), x2=max(xs), z1=min(zs), z2=max(zs), area=len(cells),
                                furn=len(furn), shape=shape, sig=tuple(sorted(sig.items())),
                                kinds=len(sig)))
    return out


def analyse(path, min_area=16, density=0.15):
    bp = load(path)
    rs = rooms(bp)
    def roomlike(r):   # corridors, landings and galleries (2 wide or less) are allowed to be empty
        return r["area"] >= min_area and min(r["x2"] - r["x1"], r["z2"] - r["z1"]) >= 2
    sparse = [r for r in rs if roomlike(r) and r["furn"] / r["area"] < density]
    # repeated floors: same room shape and same furniture at different heights (same x/z)
    rep = []
    key = Counter((r["x1"], r["z1"], r["shape"], r["sig"]) for r in rs if roomlike(r))
    for r in rs:
        if roomlike(r) and key[(r["x1"], r["z1"], r["shape"], r["sig"])] >= 2:
            rep.append(r)
    return bp, rs, sparse, rep


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--"))
    min_area = int(opts.get("min-area", 16))
    dens = float(opts.get("density", 0.15))
    files = []
    for a in args:
        p = Path(a)
        files += sorted(p.rglob("*.blueprint")) if p.is_dir() else [p]
    tot_s = tot_r = 0
    for f in files:
        try:
            bp, rs, sparse, rep = analyse(f, min_area, dens)
        except Exception as e:
            print(f"{f}: ERROR {e}")
            continue
        tot_s += len(sparse)
        tot_r += len(rep)
        for r in sparse:
            print(f"{f}: SPARSE room y={r['y']} x{r['x1']}-{r['x2']} z{r['z1']}-{r['z2']} area {r['area']} "
                  f"furniture {r['furn']} ({r['furn'] / r['area']:.2f}/cell)")
        seen = set()
        for r in rep:
            k = (r["x1"], r["z1"], r["shape"], r["sig"])
            if k in seen:
                continue
            seen.add(k)
            ys = sorted(q["y"] for q in rep if (q["x1"], q["z1"], q["shape"], q["sig"]) == k)
            print(f"{f}: REPEATED floor plan x{r['x1']}-{r['x2']} z{r['z1']}-{r['z2']} area {r['area']} "
                  f"identical at y={ys}")
    print(f"total: {tot_s} sparse rooms, {tot_r} repeated-floor rooms in {len(files)} files")


if __name__ == "__main__":
    main()
