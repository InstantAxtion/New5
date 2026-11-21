"""
Build hand-made designs into a scratch folder, check them and render a contact sheet per type.

usage: python preview.py <out dir> <type> [<type> ...] [--packs=Neoterra,Hearthwood,Cascadia] [--levels=1,3,5]

For every type: <out>/<type>.png  (rows = packs; per level: street view, back view, and a cutaway of each floor
seen from above at an angle, roof removed), plus the .blueprint files under <out>/<pack>/<rel>.
Prints requirement errors, invalid block states and unreachable beds / work blocks.
"""
from __future__ import annotations

import copy
import json
import sys
import traceback
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent))
import hm  # noqa: E402
import render  # noqa: E402
import walkcheck  # noqa: E402
from blueprint import AIR, parse_state  # noqa: E402

BLOCKS = None
for cand in (Path("/tmp/claude-0/-home-user-New5/d6177730-cb9f-5d18-81bb-de5acb2fa842/scratchpad/mcdata/blocks121.json"),
             HERE / "blocks121.json"):
    if cand.exists():
        BLOCKS = {b["name"]: b for b in json.loads(cand.read_text())}
        break


def check_states(bp):
    if BLOCKS is None:
        return []
    bad = set()
    for *_, s in bp.blocks():
        name, props = parse_state(s)
        ns, n = name.split(":")
        if ns != "minecraft":
            continue
        b = BLOCKS.get(n)
        if b is None:
            bad.add(f"unknown block {n}")
            continue
        allowed = {st["name"]: st for st in b.get("states", [])}
        for k, v in props.items():
            st = allowed.get(k)
            if st is None:
                bad.add(f"{n}: no property {k}")
            elif st["type"] == "enum" and v not in st["values"]:
                bad.add(f"{n}: {k}={v} not in {st['values']}")
            elif st["type"] == "bool" and v not in ("true", "false"):
                bad.add(f"{n}: {k}={v}")
    return sorted(bad)


def cut(bp, ytop):
    """Copy with everything above ytop removed (to look into a floor)."""
    c = copy.copy(bp)
    c.grid = [row if y <= ytop else [[AIR] * bp.sx for _ in range(bp.sz)] for y, row in enumerate(bp.grid)]
    c.tile_entities = {p: t for p, t in bp.tile_entities.items() if p[1] <= ytop}
    return c


def floors(bp, gy):
    """Floor levels: y values (above ground) where many interior cells have air over a solid block."""
    out = [gy + 1]
    for y in range(gy + 3, bp.sy - 2):
        n = 0
        for z in range(1, bp.sz - 1):
            for x in range(1, bp.sx - 1):
                if bp.get(x, y, z) == AIR and bp.get(x, y + 1, z) == AIR and bp.get(x, y - 1, z) != AIR \
                        and bp.get(x, y - 2, z) == AIR:
                    n += 1
        if n >= 12 and y - out[-1] >= 3:
            out.append(y)
    return out


def tile(img, h):
    if img.height > h:
        img = img.resize((int(img.width * h / img.height), h), Image.LANCZOS)
    return img


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--"))
    out = Path(args[0])
    packs = opts.get("packs", "Neoterra,Hearthwood,Cascadia").split(",")
    levels = [int(v) for v in opts.get("levels", "1,2,3,4,5").split(",")]
    designs = hm.load_designs()
    ok = True
    for base in args[1:]:
        fn = designs.get(base)
        if fn is None:
            print(f"{base}: no design")
            ok = False
            continue
        rows = []
        growth_need = 1.5
        for pack in packs:
            row = []
            counts = []
            for rel in hm.rels_for(base):
                L = hm.REQ[rel]["level"]
                try:
                    d = fn(pack, rel, L)
                    bp = d.finish()
                except Exception as e:
                    print(f"{base} {pack} L{L}: ERROR {e}")
                    traceback.print_exc(limit=3)
                    ok = False
                    continue
                dst = out / pack / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                bp.save(dst)
                req = hm.REQ[rel]
                if req.get("children"):
                    try:
                        bp_show = hm.assemble(d, bp, designs)
                    except Exception as e:
                        print(f"{base} {pack} L{L}: ASSEMBLY ERROR {e}")
                        ok = False
                        continue
                else:
                    bp_show = bp
                probs = [] if req.get("child") else walkcheck.analyse(bp_show)[1]
                if not req.get("child") and L in hm.PREMIUM_CAP:
                    share = hm.premium_share(bp_show, d.gy)
                    if share > hm.PREMIUM_CAP[L]:
                        print(f"{base} {pack} L{L}: PREMIUM TOO HIGH {share:.0%} > {hm.PREMIUM_CAP[L]:.0%} "
                              f"(quartz/copper/prismarine/blackstone/sea lantern/... – see hm.PREMIUM)")
                        ok = False
                counts.append((L, sum(1 for _x, _y, _z, st in bp_show.blocks()
                                      if _y != d.gy and st != AIR and "substitution" not in st)))
                bad = check_states(bp)
                status = f"{bp.sx}x{bp.sy}x{bp.sz}" + (" (assembled with child huts)" if bp_show is not bp else "")
                if probs:
                    status += f"  UNREACHABLE: {probs[:4]}"
                    ok = False
                if bad:
                    status += f"  BAD STATES: {bad[:6]}"
                    ok = False
                print(f"{base} {pack} L{L}: {status}")
                if L not in levels:
                    continue
                pre = out / "img" / f"{pack}_{Path(rel).stem}"
                pre.parent.mkdir(parents=True, exist_ok=True)
                bp = bp_show
                render.iso(bp, 2, f"{pre}_front.png", scale=10)
                render.iso(bp, 0, f"{pre}_back.png", scale=10)
                imgs = [Image.open(f"{pre}_front.png"), Image.open(f"{pre}_back.png")]
                for i, fy in enumerate(floors(bp, d.gy)):
                    p = f"{pre}_floor{i}.png"
                    render.iso(cut(bp, fy + 1), 2, p, scale=12)
                    imgs.append(Image.open(p))
                row.append((f"{pack} L{L}", imgs))
            if not hm.REQ[hm.rels_for(base)[0]].get("child"):
                cs = sorted(counts)
                line = " -> ".join(str(c) for _, c in cs)
                bad = [f"L{a}->L{b} x{cb / ca:.2f}" for (a, ca), (b, cb) in zip(cs, cs[1:]) if cb < growth_need * ca]
                print(f"{base} {pack} blocks per level: {line}" + (f"  GROWTH TOO SMALL: {', '.join(bad)}" if bad else "  growth ok"))
                if bad:
                    ok = False
            rows.append(row)
        # contact sheet
        H = 300
        lines = []
        for row in rows:
            for label, imgs in row:
                ims = [tile(i.convert("RGB"), H) for i in imgs]
                w = sum(i.width for i in ims) + 10 * len(ims)
                canvas = Image.new("RGB", (w + 10, H + 24), (255, 255, 255))
                ImageDraw.Draw(canvas).text((6, 4), label, fill=(0, 0, 0))
                x = 6
                for i in ims:
                    canvas.paste(i, (x, 22))
                    x += i.width + 10
                lines.append(canvas)
        if lines:
            W = max(l.width for l in lines)
            sheet = Image.new("RGB", (W, sum(l.height for l in lines)), (255, 255, 255))
            y = 0
            for l in lines:
                sheet.paste(l, (0, y))
                y += l.height
            sheet.save(out / f"{base}.png")
            print(f"sheet: {out / (base + '.png')}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
