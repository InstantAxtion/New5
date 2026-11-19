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
    "hopper": (70, 70, 75), "dark_oak_sapling": (50, 80, 30), "oak_leaves": (70, 120, 40),
    "waxed_cut_copper": (190, 105, 75), "light_gray_concrete": (150, 150, 145), "sand": (220, 205, 150), "black_concrete": (8, 10, 15), "redstone_block": (170, 20, 10),
    "red_bed": (160, 40, 40), "carved_pumpkin": (200, 120, 30), "blockhutfield": (180, 140, 80),
    "iron_trapdoor": (200, 200, 200), "stone_brick_wall": (120, 120, 120), "polished_deepslate_wall": (72, 72, 74), "stripped_spruce_wood": (150, 112, 70), "oak_sapling": (70, 120, 40), "birch_sapling": (110, 150, 70), "spruce_sapling": (50, 80, 50),
    "jungle_sapling": (60, 130, 40), "acacia_sapling": (110, 130, 40), "cherry_sapling": (220, 150, 180),
    "stripped_spruce_log": (150, 112, 70), "polished_diorite": (200, 200, 200), "polished_granite": (160, 110, 90),
    "stone_bricks": (120, 120, 120), "calcite": (225, 225, 220), "polished_tuff": (100, 105, 95), "piston": (150, 130, 90),
    "observer": (90, 90, 90), "dispenser": (110, 110, 110), "waxed_copper_bulb": (240, 170, 90),
    "waxed_copper_block": (190, 105, 75), "target": (220, 200, 180), "hay_block": (200, 170, 40),
    "red_bed": (160, 40, 40), "white_bed": (230, 230, 230), "red_carpet": (160, 40, 40), "blue_carpet": (50, 60, 160),
    "white_carpet": (230, 230, 230), "yellow_carpet": (240, 200, 60), "green_carpet": (90, 120, 40), "obsidian": (25, 18, 40), "iron_block": (220, 220, 222), "beacon": (120, 220, 215),
    "composter": (110, 80, 45), "wheat": (200, 180, 80), "beetroots": (150, 60, 60), "blast_furnace": (90, 90, 95),
    "decorationcontroller": (255, 60, 200), "blocksubstitution": (230, 120, 230), "birch_door": (215, 200, 150), "farmland": (100, 70, 45),
    "carrots": (90, 160, 50), "potatoes": (110, 150, 60), "cyan_bed": (21, 137, 145),
    "blockhutcitizen": (255, 60, 200), "jukebox": (110, 75, 55), "smoker": (90, 85, 80), "quartz_pillar": (232, 226, 218), "quartz_block": (235, 229, 222),
}
SOLID_GUESS = (180, 120, 200)

DYE = {"white": (233, 236, 236), "light_gray": (142, 142, 134), "gray": (62, 68, 71), "black": (20, 21, 25),
       "brown": (114, 71, 40), "red": (160, 39, 34), "orange": (240, 118, 19), "yellow": (248, 197, 39),
       "lime": (112, 185, 25), "green": (84, 109, 27), "cyan": (21, 137, 145), "light_blue": (58, 175, 217),
       "blue": (53, 57, 157), "purple": (121, 42, 172), "magenta": (189, 68, 179), "pink": (237, 141, 172)}
TERRA = {"white": (209, 178, 161), "light_gray": (135, 106, 97), "gray": (57, 42, 35), "black": (37, 22, 16),
         "brown": (77, 51, 35), "red": (143, 61, 46), "orange": (161, 83, 37), "yellow": (186, 133, 35),
         "lime": (103, 117, 52), "green": (76, 83, 42), "cyan": (86, 91, 91), "light_blue": (113, 108, 137),
         "blue": (74, 59, 91), "purple": (118, 70, 86), "magenta": (149, 88, 108), "pink": (161, 78, 78)}
WOOD = {"oak": (162, 130, 78), "spruce": (114, 84, 48), "birch": (192, 175, 121), "jungle": (160, 115, 80),
        "acacia": (168, 90, 50), "dark_oak": (66, 43, 20), "mangrove": (117, 54, 48), "cherry": (226, 178, 172),
        "bamboo": (193, 173, 80), "crimson": (101, 48, 70), "warped": (43, 104, 99)}
NAMED = {"honeycomb": (229, 148, 29), "bee_nest": (202, 160, 74), "purpur": (169, 125, 169), "amethyst": (133, 97, 191),
         "end_stone": (219, 222, 158), "nether_brick": (44, 21, 26), "red_nether": (69, 7, 9), "shroomlight": (240, 146, 70),
         "ochre_froglight": (250, 245, 206), "mud_brick": (137, 104, 79), "packed_mud": (142, 106, 79), "mud": (60, 57, 61),
         "moss": (89, 109, 45), "mossy": (115, 121, 105), "sandstone": (216, 203, 155), "red_sandstone": (186, 99, 29),
         "copper": (190, 110, 80), "exposed": (161, 125, 103), "weathered": (108, 153, 110), "oxidized": (82, 162, 132),
         "iron_block": (220, 220, 220), "gold_block": (246, 208, 61), "tinted": (43, 38, 46), "crying": (32, 10, 60),
         "blackstone": (42, 35, 40), "hay": (166, 136, 38), "bricks": (150, 97, 83), "cobble": (122, 122, 122),
         "stone": (125, 125, 125), "nylium": (130, 31, 31), "crimson_roots": (126, 8, 41), "crimson_fungus": (141, 44, 30),
         "dead_bush": (107, 79, 40), "tall_grass": (90, 140, 50), "large_fern": (80, 125, 45), "sweet_berry": (60, 100, 40),
         "lily_pad": (30, 110, 40), "redstone_lamp": (95, 54, 30), "bell": (250, 210, 60), "campfire": (100, 70, 40),
         "lantern": (220, 170, 90), "magma": (140, 60, 20), "calcite": (223, 224, 220), "glass": (200, 220, 230),
         "wool": (233, 236, 236), "coarse_dirt": (119, 85, 59), "gravel": (131, 127, 126), "amethyst_bud": (160, 120, 220),
         "ladder": (150, 120, 70), "chain": (60, 65, 80), "bars": (140, 140, 140), "barrel": (140, 100, 60)}


def guess_color(name):
    """Best-effort colour for blocks without an explicit entry (keeps previews honest)."""
    base = name.replace("_stairs", "").replace("_slab", "").replace("_wall", "")
    for d in sorted(DYE, key=len, reverse=True):
        if base.startswith(d + "_"):
            if "terracotta" in base:
                return TERRA[d]
            if "stained_glass" in base:
                r, g, b = DYE[d]
                return (min(255, r + 40), min(255, g + 40), min(255, b + 40))
            return DYE[d]
    if base == "terracotta":
        return (152, 94, 67)
    for k in sorted(NAMED, key=len, reverse=True):
        if k in base:
            return NAMED[k]
    for w in sorted(WOOD, key=len, reverse=True):
        if w in base:
            return WOOD[w]
    return SOLID_GUESS
GLASS = {"light_blue_stained_glass", "glass_pane", "glass", "tinted_glass", "blockpaperwall", "water"}
HALF = {"smooth_quartz_slab", "smooth_stone_slab", "rail", "daylight_detector"}
COLORS.update({
    "basalt": (80, 80, 86), "smooth_basalt": (72, 72, 78), "polished_basalt": (98, 98, 102), "andesite": (136, 136, 136),
    "spruce_planks": (114, 84, 48), "mossy_cobblestone": (110, 118, 95), "stripped_spruce_log": (115, 89, 52),
    "light_gray_terracotta": (135, 106, 97), "gray_terracotta": (57, 42, 35),
    "stone_brick_stairs": (122, 121, 122), "bamboo_mosaic": (190, 170, 80), "stripped_bamboo_block": (192, 175, 85),
    "chiseled_bookshelf": (150, 110, 60), "white_candle": (230, 230, 220), "spore_blossom": (210, 100, 160),
    "azalea": (100, 125, 50), "flowering_azalea": (120, 110, 80),
    "light_blue_stained_glass_pane": (130, 190, 230), "cyan_stained_glass_pane": (76, 127, 153),
    "tuff_bricks": (98, 103, 95), "polished_tuff": (97, 104, 99), "chiseled_tuff": (93, 99, 93), "bone_block": (229, 225, 207),
    "deepslate_tiles": (54, 54, 55), "polished_blackstone_bricks": (48, 42, 49), "white_glazed_terracotta": (188, 212, 202),
    "stripped_warped_stem": (57, 150, 147), "pearlescent_froglight": (245, 240, 239), "verdant_froglight": (229, 244, 228),
    "stone_bricks": (122, 121, 122), "polished_diorite_stairs": (193, 193, 195), "smooth_quartz_stairs": (235, 229, 222),
    "potted_fern": (120, 140, 70), "potted_azalea_bush": (120, 140, 70), "potted_flowering_azalea_bush": (120, 140, 70), "potted_bamboo": (120, 140, 70), "potted_oak_sapling": (120, 140, 70), "potted_lily_of_the_valley": (120, 140, 70), "potted_cornflower": (120, 140, 70), "potted_blue_orchid": (120, 140, 70), "potted_cactus": (120, 140, 70), "potted_birch_sapling": (120, 140, 70),
    "calcite": (223, 224, 220), "diorite": (188, 188, 188), "polished_diorite": (193, 193, 195), "birch_planks": (192, 175, 121),
    "smooth_quartz": (235, 229, 222), "quartz_bricks": (234, 229, 221), "chiseled_quartz_block": (231, 226, 218),
    "quartz_pillar": (236, 231, 224), "cyan_terracotta": (87, 91, 91), "waxed_oxidized_cut_copper": (80, 154, 132),
    "waxed_oxidized_copper": (82, 162, 132), "waxed_oxidized_copper_grate": (82, 162, 132),
    "prismarine_bricks": (99, 171, 158), "dark_prismarine": (51, 91, 75), "cyan_stained_glass": (76, 127, 153),
    "white_stained_glass": (230, 235, 240), "polished_deepslate": (72, 72, 73), "moss_block": (89, 109, 45),
    "moss_carpet": (89, 109, 45), "flowering_azalea_leaves": (100, 111, 61), "azalea_leaves": (90, 115, 44),
    "vine": (60, 100, 30), "daylight_detector": (130, 116, 94), "iron_trapdoor": (200, 200, 200),
    "stripped_birch_log": (196, 176, 118), "stripped_oak_log": (177, 144, 86), "pink_petals": (240, 160, 200),
    "lilac": (190, 140, 200), "rose_bush": (160, 30, 30), "peony": (230, 180, 220), "red_tulip": (200, 40, 40),
    "white_tulip": (240, 240, 240), "orange_tulip": (230, 120, 30), "pink_tulip": (240, 160, 200),
    "white_carpet": (233, 236, 236), "light_blue_carpet": (58, 175, 217), "cyan_carpet": (21, 137, 145),
    "light_gray_carpet": (142, 142, 134), "short_grass": (80, 140, 50), "chain": (60, 65, 80),
    "gate_iron": (90, 95, 100), "blockminecoloniesnamedgrave": (150, 150, 155), "decorationcontroller": (200, 200, 200),
    "amethyst_block": (133, 97, 191), "amethyst_cluster": (160, 120, 220), "obsidian": (20, 18, 30), "crying_obsidian": (40, 10, 70),
    "soul_lantern": (90, 200, 210), "soul_sand": (81, 62, 50), "netherrack": (110, 50, 50), "moss_block": (89, 109, 45),
    "polished_blackstone": (53, 48, 56), "bookshelf": (120, 90, 50), "enchanting_table": (60, 20, 60), "lectern": (170, 130, 80),
    "lily_pad": (30, 110, 40), "rail": (110, 100, 80), "beacon": (120, 220, 220),
    "coarse_dirt": (119, 85, 59), "dirt": (134, 96, 67), "mud": (60, 57, 61), "composted_dirt": (70, 50, 35),
    "soul_sand": (81, 62, 50), "nether_wart": (150, 30, 35), "cobblestone": (122, 122, 122),
    "red_concrete": (142, 32, 32), "blue_concrete": (44, 46, 143), "lime_concrete": (94, 168, 24),
    "magenta_concrete": (169, 48, 159), "purple_concrete": (100, 31, 156),
    "barrel_block": (140, 100, 60), "beehive": (190, 150, 90), "magma_block": (140, 60, 20),
    "fern": (80, 130, 50), "poppy": (200, 30, 30), "dandelion": (240, 220, 40), "cornflower": (70, 100, 220),
    "allium": (180, 110, 220), "azure_bluet": (220, 230, 240), "oxeye_daisy": (240, 240, 230),
    "lily_of_the_valley": (245, 245, 245), "cave_vines": (90, 110, 40), "campfire": (100, 70, 40),
    "birch_fence_gate": (200, 180, 120), "fletching_table": (180, 160, 110), "loom": (150, 120, 90),
    "grindstone": (140, 140, 140), "brewing_stand": (120, 100, 80), "water_cauldron": (60, 90, 200),
    "cyan_stained_glass": (60, 130, 150), "lime_stained_glass": (120, 200, 40),
    "magenta_stained_glass": (190, 80, 180), "yellow_stained_glass": (230, 220, 50),
})


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
        if s == "blockfluidsubstitution":
            return "water"
        return None if s in ("air", "blocksubstitution", "blocktagsubstitution") else s

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
        c = COLORS.get(base) or COLORS.get(base.replace("_stairs", "").replace("_slab", "")) or guess_color(base)
        a = 120 if b in GLASS or "glass" in b else (150 if b == "water" else 255)
        top = 0.5 if (b in HALF or "slab" in b) else 1.0
        if b == "rail":
            top = 0.1
        yb = y
        if "slab" in b:
            ox_, oz_ = orig(x, z)
            if "type=top" in bp.grid[y][oz_][ox_]:
                yb, top = y + 0.5, 1.0                    # top slab: upper half of the block
        yt = y + top

        def nb(dx, dy, dz):
            n = at(x + dx, y + dy, z + dz)
            return n is not None and n not in GLASS and n not in HALF and b not in GLASS

        faces = []
        if not nb(0, 1, 0) or top < 1:
            faces.append(([P(x, yt, z), P(x + 1, yt, z), P(x + 1, yt, z + 1), P(x, yt, z + 1)], 1.0))
        if not nb(1, 0, 0):
            faces.append(([P(x + 1, yt, z), P(x + 1, yt, z + 1), P(x + 1, yb, z + 1), P(x + 1, yb, z)], 0.78))
        if not nb(0, 0, 1):
            faces.append(([P(x, yt, z + 1), P(x + 1, yt, z + 1), P(x + 1, yb, z + 1), P(x, yb, z + 1)], 0.62))
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
                    col = COLORS.get(s) or guess_color(s)
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
                    col = COLORS.get(s) or guess_color(s)
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
