"""
Renders isometric previews and a floor plan of a .blueprint file (approximate block colours).

usage: python render.py file.blueprint out_prefix
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
from blueprint import load, parse_state  # noqa: E402

COLORS = {
    "stone": (125, 125, 125), "smooth_stone": (158, 158, 158), "gravel": (131, 127, 126),
    "polished_andesite": (132, 135, 134), "light_gray_concrete": (125, 125, 115),
    "white_concrete": (207, 213, 214), "gray_concrete": (55, 58, 62), "black_concrete": (8, 10, 15),
    "yellow_concrete": (241, 175, 21), "orange_concrete": (224, 97, 1),
    "light_blue_stained_glass": (102, 153, 216), "glass_pane": (200, 225, 235),
    "smooth_quartz": (235, 229, 222), "smooth_quartz_slab": (235, 229, 222),
    "smooth_quartz_stairs": (225, 219, 212), "smooth_stone_slab": (158, 158, 158),
    "polished_andesite_stairs": (132, 135, 134), "sea_lantern": (172, 214, 202),
    "rail": (110, 90, 60), "dark_oak_stairs": (66, 43, 20), "moss_block": (89, 110, 45),
    "flowering_azalea": (112, 135, 60), "polished_blackstone_wall": (53, 48, 56),
    "lantern": (230, 170, 80),
    "blocksolidsubstitution": (120, 90, 60), "grass_block": (95, 150, 60), "cyan_concrete": (21, 119, 136),
    "light_gray_concrete": (125, 125, 115), "polished_deepslate": (72, 72, 74), "tinted_glass": (60, 50, 70),
    "glass": (200, 225, 235), "water": (60, 90, 220), "soul_sand": (80, 60, 50), "bookshelf": (120, 90, 55),
    "barrel": (120, 85, 50), "crafting_table": (130, 95, 60), "furnace": (110, 110, 110), "white_bed": (230, 230, 230),
    "cyan_bed": (21, 137, 145), "azalea": (100, 125, 50), "waxed_cut_copper": (190, 105, 75),
    "waxed_copper_door": (190, 105, 75), "end_rod": (240, 235, 220), "lightning_rod": (190, 105, 75),
    "smooth_quartz": (235, 229, 222), "enchanting_table": (150, 30, 40), "blockhuttownhall": (255, 60, 200),
    "spruce_planks": (115, 85, 50), "stripped_spruce_log": (150, 112, 70), "spruce_stairs": (115, 85, 50),
    "light_gray_stained_glass": (175, 180, 185), "oak_leaves": (70, 120, 40), "azalea_leaves": (90, 125, 45),
    "stripped_oak_log": (175, 140, 85), "daylight_detector": (50, 60, 90), "chain": (60, 65, 75),
    "short_grass": (110, 160, 70), "light_gray_bed": (160, 160, 155), "polished_blackstone_wall": (53, 48, 56),
    "blockminecoloniesrack": (140, 100, 60), "blockhutwarehouse": (255, 60, 200),
    "blockhutdeliveryman": (255, 60, 200), "ladder": (150, 115, 70), "moss_carpet": (89, 110, 45),
    "yellow_concrete": (241, 175, 21), "bricks": (150, 75, 60), "spruce_fence": (115, 85, 50),
    "architectscutter": (150, 120, 90), "blockhutbuilder": (255, 60, 200), "iron_bars": (120, 120, 120),
    "stonecutter": (120, 120, 120), "anvil": (60, 60, 60), "smithing_table": (60, 50, 50),
    "hopper": (70, 70, 75),
}
SOLID_GUESS = (180, 120, 200)
GLASS = {"light_blue_stained_glass", "glass_pane", "glass", "tinted_glass", "blockpaperwall", "water"}
HALF = {"smooth_quartz_slab", "smooth_stone_slab", "rail", "daylight_detector"}


def short(state):
    return parse_state(state)[0].split(":")[1]


def material(bp, x, y, z):
    """Short name used for colouring; Domum Ornamentum blocks use their main material."""
    s = short(bp.grid[y][z][x])
    te = bp.tile_entities.get((x, y, z))
    if te is not None and "textureData" in te:
        m = str(te["textureData"].get("minecraft:block/oak_planks", "")).split(":")[-1]
        if s.endswith("light"):
            return "sea_lantern"
        if s == "blockpaperwall":
            return "glass_pane"
        if s.endswith("slab_compat"):
            return m + "_slab_do"
        return m or s
    return s


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def iso(bp, rot, path, scale=14):
    """rot: 0..3 quarter turns; viewer sits on the +x'/+z' side after rotation."""
    sx, sy, sz = bp.sx, bp.sy, bp.sz

    # build rotated grid explicitly
    W, D = (sx, sz) if rot % 2 == 0 else (sz, sx)

    def orig(x, z):
        if rot == 0:
            return x, z
        if rot == 1:
            return sx - 1 - z, x
        if rot == 2:
            return sx - 1 - x, sz - 1 - z
        return z, sz - 1 - x

    def at(x, y, z):
        if not (0 <= x < W and 0 <= z < D and 0 <= y < sy):
            return None
        ox, oz = orig(x, z)
        s = material(bp, ox, y, oz)
        return None if s == "air" else s

    w, h, H = scale, scale / 2, scale * 1.15
    img_w = int((W + D) * w + 40)
    img_h = int((W + D) * h + sy * H + 40)
    img = Image.new("RGBA", (img_w, img_h), (236, 240, 244, 255))
    dr = ImageDraw.Draw(img, "RGBA")
    ox0 = D * w + 20
    oy0 = sy * H + 20

    def P(x, y, z):
        return (ox0 + (x - z) * w, oy0 + (x + z) * h - y * H)

    order = sorted(((x, y, z) for x in range(W) for y in range(sy) for z in range(D)),
                   key=lambda p: (p[0] + p[2], p[1]))
    for x, y, z in order:
        b = at(x, y, z)
        if b is None:
            continue
        base = b[:-8] if b.endswith("_slab_do") else b
        c = COLORS.get(base) or COLORS.get(base.replace("_stairs", "").replace("_slab", "")) or SOLID_GUESS
        a = 120 if b in GLASS or "glass" in b else (150 if b == "water" else 255)
        top = 0.5 if (b in HALF or "slab" in b) else 1.0
        if b == "rail":
            top = 0.1
        yt = y + top

        def nb(dx, dy, dz):
            n = at(x + dx, y + dy, z + dz)
            return n is not None and n not in GLASS and n not in HALF and b not in GLASS

        faces = []
        if not nb(0, 1, 0) or top < 1:
            faces.append(([P(x, yt, z), P(x + 1, yt, z), P(x + 1, yt, z + 1), P(x, yt, z + 1)], 1.0))
        if not nb(1, 0, 0):
            faces.append(([P(x + 1, yt, z), P(x + 1, yt, z + 1), P(x + 1, y, z + 1), P(x + 1, y, z)], 0.78))
        if not nb(0, 0, 1):
            faces.append(([P(x, yt, z + 1), P(x + 1, yt, z + 1), P(x + 1, y, z + 1), P(x, y, z + 1)], 0.62))
        for poly, k in faces:
            dr.polygon(poly, fill=shade(c, k) + (a,), outline=shade(c, k * 0.85) + (min(255, a + 40),))
    img = img.crop(img.getbbox())
    img.save(path)


def plan(bp, path, cell=16):
    """Top-down plan: highest non-roof block up to y=4 (shows interior layout)."""
    img = Image.new("RGB", (bp.sx * cell, bp.sz * cell), (255, 255, 255))
    dr = ImageDraw.Draw(img)
    for z in range(bp.sz):
        for x in range(bp.sx):
            col = (255, 255, 255)
            for y in range(4, -1, -1):
                s = material(bp, x, y, z)
                if s != "air":
                    col = COLORS.get(s, SOLID_GUESS)
                    break
            dr.rectangle([x * cell, z * cell, (x + 1) * cell - 1, (z + 1) * cell - 1], fill=col, outline=(200, 200, 200))
    img.save(path)


def plan_at(bp, path, y_top, cell=12):
    """Top-down plan showing the highest block at or below y_top."""
    img = Image.new("RGB", (bp.sx * cell, bp.sz * cell), (255, 255, 255))
    dr = ImageDraw.Draw(img)
    for z in range(bp.sz):
        for x in range(bp.sx):
            col = (255, 255, 255)
            for y in range(y_top, -1, -1):
                s = material(bp, x, y, z)
                if s != "air":
                    col = COLORS.get(s, SOLID_GUESS)
                    if y < y_top - 1:
                        col = shade(col, 0.55)
                    break
            dr.rectangle([x * cell, z * cell, (x + 1) * cell - 1, (z + 1) * cell - 1], fill=col, outline=(210, 210, 210))
    img.save(path)


if __name__ == "__main__":
    src, prefix = sys.argv[1], sys.argv[2]
    bp = load(src)
    if len(sys.argv) > 3:
        for yt in map(int, sys.argv[3].split(",")):
            plan_at(bp, f"{prefix}_plan_y{yt}.png", yt)
    iso(bp, 2, f"{prefix}_front.png")   # viewer at the street side (north-west)
    iso(bp, 0, f"{prefix}_back.png")    # viewer behind the platforms (south-east)
    plan(bp, f"{prefix}_plan.png")
    print("rendered", prefix)
