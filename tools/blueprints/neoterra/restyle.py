"""
Hearthwood – a cozy modern style pack derived from the finished Neoterra pack.

Same buildings, levels, hut requirements and paths as Neoterra (so every hut works the same), but
re-materialised for a warm, cozy modern feel:

  walls      warm plaster (white terracotta) with vertical wood-cladding panels, stone-brick base course
  trim       dark wood (dark oak / spruce logs), stone bricks
  roofs      spruce / dark oak stairs and slabs, stone-brick or tiled flat roofs
  floors     wood plank floors inside, stone-brick / cobble aprons outside
  accents    one cozy palette per building: terracotta, brick, sage, rose, honey, walnut, slate, plum
  light      lanterns and glowstone (froglights at level 5), warm rugs

Levels 1-4 use only easy-to-medium blocks (planks, logs, stone, bricks, terracotta, wool, glass,
copper, glowstone, mud bricks ...). Level 5 may use anything (deepslate, cherry, froglights, ...).
Block entities, tags and every functional block (beds, furnaces, racks, portals, crops ...) are
left as they are; Domum Ornamentum blocks get their textures re-mapped the same way.

usage: python restyle.py <neoterra-pack-dir> <out-pack-dir> [Hearthwood|Cascadia]
"""
from __future__ import annotations

import hashlib
import re
import shutil
import sys
from multiprocessing import Pool
from pathlib import Path

from nbtlib import tag as NBT

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from blueprint import load, parse_state, format_state, AIR  # noqa: E402
import themes  # noqa: E402

PACK = "Hearthwood"          # overwritten per style in main()

# per style: shared surface materials as (levels 1-4, level 5) lists; one is picked per block by position
STYLE_MATS = {
    "Hearthwood": dict(
        apron=(["stone_bricks", "stone_bricks", "stone_bricks", "cobblestone"], ["stone_bricks", "cobblestone"]),
        roof=(["stone_bricks"], ["deepslate_tiles"]),
        base=(["stone_bricks"], ["deepslate_bricks"]),
        plaster=(["white_terracotta"], ["white_terracotta", "white_terracotta", "calcite"]),
        clad=.38, light=("glowstone", "ochre_froglight"),
        desc="Cozy modern: warm plaster and wood cladding, brick, terracotta and lantern light. Same buildings as "
             "Neoterra, levels 1-4 built from easy-to-medium blocks, level 5 from anything."),
    "Cascadia": dict(
        apron=(["cobblestone", "mossy_cobblestone", "andesite", "cobblestone"], ["mossy_cobblestone", "smooth_basalt", "cobblestone"]),
        roof=(["moss_block", "moss_block", "mossy_cobblestone"], ["moss_block", "moss_block", "smooth_basalt"]),
        base=(["cobblestone", "mossy_cobblestone", "andesite"], ["polished_basalt[axis=y]", "smooth_basalt", "mossy_cobblestone"]),
        plaster=(["spruce_planks", "spruce_planks", "light_gray_terracotta"], ["spruce_planks", "stripped_spruce_log[axis=y]"]),
        clad=.55, light=("glowstone", "shroomlight"),
        desc="Pacific Northwest / Oregon: cedar and fir timber, river-rock bases, mossy roofs, covered-bridge red, "
             "coast teal and basalt at the top level. Same buildings as Neoterra, levels 1-4 from easy-to-medium "
             "blocks, level 5 from anything."),
}
STYLE_PALETTES = {
    "Cascadia": {
        "fir":      (["green_terracotta", "moss_block"], ["moss_block", "mossy_stone_bricks"]),
        "bridge":   (["red_terracotta", "red_wool"], ["red_terracotta", "red_nether_bricks"]),
        "coast":    (["cyan_terracotta", "light_gray_terracotta"], ["cyan_terracotta", "waxed_oxidized_cut_copper"]),
        "rain":     (["light_gray_terracotta", "gray_terracotta"], ["smooth_basalt", "light_gray_terracotta"]),
        "timber":   (["brown_terracotta", "dark_oak_planks"], ["dark_oak_planks", "mangrove_planks"]),
        "wheat":    (["yellow_terracotta", "hay_block"], ["yellow_terracotta", "bamboo_planks"]),
        "wool":     (["red_wool", "orange_wool", "yellow_wool", "lime_wool", "cyan_wool", "light_blue_wool"],
                     ["red_wool", "orange_wool", "yellow_wool", "lime_wool", "cyan_wool", "light_blue_wool"]),
    },
}
STYLE_THEME_MAP = {
    "Cascadia": {
        "forge": "bridge", "garden": "fir", "bloom": "fir", "arcane": "rain", "scholar": "timber", "civic": "wheat",
        "medical": "bridge", "harvest": "wheat", "timber": "timber", "industrial": "rain", "earth": "timber",
        "rainbow": "wool", "prism": "coast", "military": "rain", "nether": "bridge", "ranch": "bridge", "wool": "rain",
        "mud": "timber", "carrot": "wheat", "coop": "wheat", "honey": "wheat", "kitchen": "bridge", "playful": "fir",
        "academy": "timber", "brick": "bridge", "luxe": "timber", "memorial": "fir", "celestial": "coast",
        "potion": "fir", "sky": "coast", "copper": "coast", "steel": "rain", "sand": "wheat", "slate": "rain",
        "bamboo": "fir", "arena": "bridge", "rust": "timber", "ocean": "coast",
    },
}
STYLE_WOODS = {
    "Cascadia": (("spruce_planks", "stripped_spruce_log", "dark_oak_log", "spruce"),
                 ("spruce_planks", "stripped_spruce_log", "dark_oak_log", "dark_oak")),
}
STYLE = "Hearthwood"
HARD = ("quartz", "deepslate", "basalt", "prismarine", "purpur", "amethyst", "end_stone", "gold_block", "iron_block",
        "nether_brick", "crimson", "warped", "blackstone", "froglight", "sea_lantern", "end_rod", "tinted_glass",
        "crying_obsidian", "shroomlight", "beacon", "cherry")

# cozy accent palettes: (levels 1-4, level 5)
PALETTES = {
    "terracotta": (["orange_terracotta", "brown_terracotta"], ["waxed_cut_copper", "orange_terracotta"]),
    "brick":      (["bricks", "terracotta"], ["bricks", "mud_bricks"]),
    "sage":       (["green_terracotta", "lime_terracotta"], ["moss_block", "mossy_stone_bricks"]),
    "rose":       (["pink_terracotta", "red_terracotta"], ["cherry_planks", "pink_terracotta"]),
    "honey":      (["yellow_terracotta", "orange_terracotta"], ["honeycomb_block", "yellow_terracotta"]),
    "walnut":     (["dark_oak_planks", "brown_terracotta"], ["dark_oak_planks", "mangrove_planks"]),
    "slate":      (["light_blue_terracotta", "cyan_terracotta"], ["deepslate_tiles", "light_blue_terracotta"]),
    "plum":       (["purple_terracotta", "magenta_terracotta"], ["purpur_block", "purple_terracotta"]),
    "wool":       (["red_wool", "orange_wool", "yellow_wool", "lime_wool", "light_blue_wool", "magenta_wool"],
                   ["red_wool", "orange_wool", "yellow_wool", "lime_wool", "light_blue_wool", "magenta_wool"]),
}
THEME_TO_PALETTE = {
    "forge": "brick", "garden": "sage", "bloom": "rose", "arcane": "plum", "scholar": "walnut", "civic": "honey",
    "medical": "brick", "harvest": "honey", "timber": "walnut", "industrial": "slate", "earth": "terracotta",
    "rainbow": "wool", "prism": "slate", "military": "slate", "nether": "brick", "ranch": "brick", "wool": "slate",
    "mud": "terracotta", "carrot": "terracotta", "coop": "honey", "honey": "honey", "kitchen": "terracotta",
    "playful": "sage", "academy": "walnut", "brick": "brick", "luxe": "walnut", "memorial": "sage",
    "celestial": "plum", "potion": "plum", "sky": "slate", "copper": "terracotta", "steel": "slate",
    "sand": "honey", "slate": "slate", "bamboo": "sage", "arena": "brick", "rust": "terracotta", "ocean": "slate",
}
# wood per palette: (cladding planks, cladding log, trim log, stairs/slab wood)  levels 1-4 / level 5
WOODS = {
    "walnut": (("dark_oak_planks", "stripped_dark_oak_log", "spruce_log", "dark_oak"),
               ("dark_oak_planks", "stripped_dark_oak_log", "dark_oak_log", "dark_oak")),
    "rose":   (("birch_planks", "stripped_birch_log", "dark_oak_log", "spruce"),
               ("cherry_planks", "stripped_cherry_log", "dark_oak_log", "cherry")),
    "sage":   (("oak_planks", "stripped_oak_log", "dark_oak_log", "spruce"),
               ("oak_planks", "stripped_oak_log", "dark_oak_log", "dark_oak")),
}
DEFAULT_WOOD = (("spruce_planks", "stripped_spruce_log", "dark_oak_log", "spruce"),
                ("spruce_planks", "stripped_spruce_log", "dark_oak_log", "dark_oak"))

WHITEISH = ("white_concrete", "calcite", "smooth_quartz", "quartz_bricks", "polished_diorite", "diorite", "bone_block",
            "white_glazed_terracotta", "chiseled_quartz_block", "birch_planks", "white_terracotta", "smooth_sandstone",
            "cut_sandstone", "sandstone", "end_stone_bricks", "white_wool", "light_gray_wool", "quartz_block")
TRIMS = ("quartz_pillar", "polished_deepslate", "deepslate_tiles", "deepslate_bricks", "gray_concrete", "black_concrete",
         "polished_tuff", "tuff_bricks", "chiseled_tuff", "polished_blackstone", "polished_blackstone_bricks",
         "iron_block", "stripped_warped_stem", "light_gray_concrete", "chiseled_stone_bricks", "cobbled_deepslate")
FLOORS = ("smooth_stone", "polished_andesite", "andesite", "stone")
LIGHTS = ("sea_lantern", "froglight", "shroomlight", "redstone_lamp", "glowstone")
ACCENT_WORDS = ("_concrete", "_terracotta", "prismarine", "copper", "purpur", "amethyst", "gold_block",
                "nether_brick", "crimson", "warped", "honeycomb", "mud_brick", "packed_mud", "moss_block", "mossy",
                "bricks", "cherry", "bamboo", "mangrove", "_planks", "_wool", "red_sandstone", "magma")
CARPETS = {"cyan_carpet": "brown_carpet", "light_blue_carpet": "orange_carpet", "white_carpet": "white_carpet",
           "light_gray_carpet": "light_gray_carpet"}
FUNCTIONAL = ("door", "ladder", "bed", "blockhut", "rack", "chest", "barrel", "furnace", "smoker", "anvil", "table",
              "cauldron", "brewing", "composter", "beehive", "bee_nest", "lectern", "grave", "loom",
              "grindstone", "stonecutter", "target", "hay_block", "composted", "farmland", "gate", "water", "lava",
              "substitution", "bell", "soul_sand", "nether_wart", "barrel_block", "decorationcontroller", "sand",
              "coarse_dirt", "cactus", "sugar", "bamboo_sapling", "kelp", "rail", "scarecrow", "field")


def hsh(*a):
    return int.from_bytes(hashlib.md5(repr(a).encode()).digest()[:4], "little") / 2 ** 32


class Restyler:
    def __init__(self, bp, level, name):
        self.bp, self.L, self.name = bp, level, name
        th = themes.recipe(name)
        pals = STYLE_PALETTES.get(STYLE, PALETTES)
        tmap = STYLE_THEME_MAP.get(STYLE, THEME_TO_PALETTE)
        key = tmap.get(th["theme"]) if th else None
        if key is None:
            keys = [k for k in pals if k != "wool"]
            key = keys[int(hsh("pal", re.sub(r"\d.*$", "", name)) * len(keys))]
        self.pal = pals[key]
        self.wood = STYLE_WOODS.get(STYLE) or WOODS.get(key, DEFAULT_WOOD)
        self.mats = STYLE_MATS[STYLE]
        self.top = level >= 5
        self.gy = 1
        for (ax, ay, az), te in bp.tile_entities.items():
            bdp = te.get("blueprintDataProvider")
            if bdp is None:
                continue
            for e in bdp.get("posTagMap", []):
                if any(str(t["tagName"]) == "groundlevel" for t in e["tagNameList"]):
                    self.gy = ay + int(e["tagPos"]["y"])
        self.protect = set(bp.tile_entities)

    # -------------------------------------------------------------- helpers
    def W(self, i):                       # wood tuple for this level
        return self.wood[1 if self.top else 0][i]

    def mat(self, key, x, y, z):
        lst = self.mats[key][1 if self.top else 0]
        v = lst[int(hsh(key, x, y, z, self.name) * len(lst))]
        name, props = (v.split("[")[0], dict(kv.split("=") for kv in v[:-1].split("[")[1].split(","))) if "[" in v else (v, {})
        return name, props

    def accent(self, x, y, z):
        lst = self.pal[1 if self.top else 0]
        return lst[int(hsh("a", x // 2, y // 2, z // 2, self.name) * len(lst))]

    def solid_above(self, x, y, z):
        s = self.bp.get(x, y + 1, z) if self.bp.inside(x, y + 1, z) else AIR
        n = parse_state(s)[0].split(":")[1]
        return n != "air" and not any(k in n for k in ("pane", "carpet", "lantern", "rod", "chain", "slab", "stairs",
                                                          "flower", "grass", "potted", "door", "ladder", "bars"))

    def covered(self, x, y, z):
        for yy in range(y + 2, min(self.bp.sy, y + 10)):
            if self.bp.get(x, yy, z) != AIR:
                return True
        return False

    # -------------------------------------------------------------- the mapping
    def map_name(self, n, x, y, z, props):
        """Return (new_name, new_props) or None to keep."""
        if n == "obsidian" or any(k in n for k in FUNCTIONAL if k != "obsidian"):
            return None
        if "amethyst_cluster" in n or "amethyst_bud" in n:
            return None if self.top else ("lantern", {"hanging": "false", "waterlogged": "false"})
        # stairs / slabs -> cozy wood
        if n.endswith("_stairs"):
            if any(w in n for w in ("spruce", "dark_oak", "oak", "birch", "cherry", "brick", "mud_brick", "cobblestone")):
                return None
            return f"{self.W(3)}_stairs", props
        if n.endswith("_slab"):
            if any(w in n for w in ("spruce", "dark_oak", "oak", "birch", "cherry", "brick", "cobblestone")):
                return None
            return f"{self.W(3)}_slab", props
        if n.endswith("_carpet"):
            return CARPETS.get(n, n), props
        if n == "end_rod":
            if self.top:
                return None
            return "lantern", {"hanging": "true" if props.get("facing") == "down" else "false", "waterlogged": "false"}
        if n == "soul_lantern":
            return "lantern", props
        if "stained_glass_pane" in n:
            return "glass_pane", props
        if "stained_glass" in n or n == "tinted_glass":
            return "glass", {}
        if any(k in n for k in LIGHTS) and n != "glowstone":
            lt = self.mats["light"][1 if self.top else 0]
            return (lt, {"axis": "y"}) if "froglight" in lt else (lt, {})
        if n.endswith("_log") or n.endswith("_stem") or n.endswith("_wood") or n == "quartz_pillar":
            if n.startswith(("stripped_spruce", "stripped_dark_oak", "dark_oak", "spruce")):
                return None
            return self.W(2), {"axis": props.get("axis", "y")}
        if n in FLOORS or n in ("light_gray_concrete",) and not self.solid_above(x, y, z):
            if not self.solid_above(x, y, z):
                if self.covered(x, y, z) and y > self.gy - 1:      # inside: plank floor with darker seams
                    return (self.W(0), {}) if z % 4 else (self.W(1), {"axis": "x"})
                if y <= self.gy:                                     # outside apron
                    return self.mat("apron", x, 0, z)
                return self.mat("roof", x, y, z)                                  # flat roof deck
            return None
        if n in WHITEISH:
            if y <= self.gy + 1:
                return self.mat("base", x, y, z)                                  # base course
            if not self.solid_above(x, y, z) and not self.covered(x, y, z):
                return self.mat("roof", x, y, z)                                  # parapet / roof surface
            if hsh("clad", x // 3, z // 3, self.name) < self.mats["clad"]:                    # vertical wood cladding panels
                return (self.W(1), {"axis": "y"}) if (x + z) % 2 else (self.W(0), {})
            return self.mat("plaster", x // 2, y // 2, z // 2)
        if n in TRIMS:
            if n == "light_gray_concrete":
                return "stone_bricks", {}
            return self.W(2), {"axis": "y"}
        if any(k in n for k in ACCENT_WORDS):
            if self.W(0) == n or n in ("stone_bricks", "cobblestone"):
                return None
            new = self.accent(x, y, z)
            return new, ({"axis": "y"} if new.endswith(("_log", "_block")) and "bamboo" in new else {})
        if not self.top and any(k in n for k in HARD):           # anything else hard-to-get below level 5
            if n.endswith("_wall"):
                return "cobblestone_wall", props
            return self.accent(x, y, z), {}
        return None

    def remap_texture(self, te, x, y, z):
        td = te.get("textureData")
        if td is None:
            return
        for k in list(td.keys()):
            v = str(td[k])
            n = v.split(":")[-1]
            res = self.map_name(n, x, y, z, {})
            if res:
                td[k] = NBT.String("minecraft:" + res[0])

    def run(self):
        bp = self.bp
        for x, y, z, s in list(bp.blocks()):
            name, props = parse_state(s)
            ns, n = name.split(":")
            if (x, y, z) in self.protect:
                te = bp.tile_entities[(x, y, z)]
                if "domum_ornamentum" in ns:
                    self.remap_texture(te, x, y, z)
                continue
            if ns != "minecraft":
                continue
            res = self.map_name(n, x, y, z, props)
            if not res:
                continue
            new, nprops = res
            bp.grid[y][z][x] = format_state("minecraft:" + new, nprops)
        # pack name in every hut / decoration / field block entity
        for te in bp.tile_entities.values():
            if str(te.get("pack", "")) == "Neoterra":
                te["pack"] = NBT.String(STYLE)
            bdp = te.get("blueprintDataProvider")
            if bdp is not None and str(bdp.get("pack", "")) == "Neoterra":
                bdp["pack"] = NBT.String(STYLE)
        bp.architects = [STYLE]
        if not self.top:
            for x, y, z, s in bp.blocks():
                if (x, y, z) not in self.protect and any(k in s for k in HARD):
                    raise AssertionError(f"{self.name}: hard block {s} at level {self.L}")


def level_of(path: Path):
    m = re.search(r"(\d+)\.blueprint$", path.name)
    if not m:
        return 4                                          # single-level decorations: easy-medium blocks
    lvl = int(m.group(1))
    if "gatehouse" in path.name or "watchtower" in path.name:
        return {1: 2, 2: 3, 3: 5}.get(lvl, 4)
    if "tavern" in path.name:
        return {1: 2, 2: 3, 3: 4}.get(lvl, 4)
    return lvl if 1 <= lvl <= 5 else 4


def process(args):
    global STYLE
    src, dst, STYLE = Path(args[0]), Path(args[1]), args[2]
    bp = load(src)
    r = Restyler(bp, level_of(src), src.stem)
    r.run()
    dst.parent.mkdir(parents=True, exist_ok=True)
    bp.save(dst)
    return dst.name


def main():
    global STYLE
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    STYLE = sys.argv[3] if len(sys.argv) > 3 else "Hearthwood"
    if dst.exists():
        shutil.rmtree(dst)
    jobs = [(str(f), str(dst / f.relative_to(src)), STYLE) for f in sorted(src.rglob("*.blueprint"))]
    with Pool() as pool:
        for _ in pool.imap_unordered(process, jobs, chunksize=2):
            pass
    import json
    (dst / "pack.json").write_text(json.dumps({
        "icon": f"{STYLE.lower()}.png",
        "name": STYLE,
        "authors": ["New5"],
        "desc": STYLE_MATS[STYLE]["desc"],
        "mods": ["structurize", "minecolonies", "domum_ornamentum"],
        "version": "1",
        "pack-format": "1",
    }, indent=2) + "\n")
    print(f"{len(jobs)} blueprints restyled -> {dst}")


if __name__ == "__main__":
    main()
