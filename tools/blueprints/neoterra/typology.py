"""
Real-world building typology for the hut generator (archgen).

Every hut type is mapped to the building it is in real life – plan, roof, storeys and the features that
make it recognisable (a town hall's portico and clock tower, a hospital's red cross and ambulance canopy,
a bakery's storefront, awning and oven chimney, a warehouse's loading docks, a barn's big doors and silo,
...). Features appear level by level; materials and roof shapes stay in each pack's own style.
"""
from __future__ import annotations

import math

AIR = "minecraft:air"

# archetype roof kind -> archgen roof form, per pack
ROOFMAP = {
    "Cascadia": {"pitched": "gable_steep", "steep": "aframe", "hip": "hip", "barn": "gambrel", "flat": "gable",
                 "industrial": "gable", "battlement": "flat"},
    "Hearthwood": {"pitched": "gable", "steep": "gable_steep", "hip": "hip", "barn": "gambrel", "flat": "hip",
                   "industrial": "shed", "battlement": "flat", "gable": "gable", "shed_roof": "shed"},
    "Neoterra": {"pitched": "shed", "steep": "gable", "hip": "flat", "barn": "gambrel", "flat": "flat",
                 "industrial": "flat", "battlement": "flat"},
}

WOOD = {"Cascadia": "spruce", "Hearthwood": "dark_oak", "Neoterra": "birch"}
STONE = {"Cascadia": "stone_bricks", "Hearthwood": "bricks", "Neoterra": "light_gray_concrete"}
FACE = {"Cascadia": "calcite", "Hearthwood": "calcite", "Neoterra": "white_concrete"}
FLAG = {"Cascadia": ["green_wool", "white_wool"], "Hearthwood": ["red_wool", "white_wool"], "Neoterra": ["cyan_wool", "white_wool"]}


def T(plan, roof, floors=None, feats=(), margin=5, skin=None, dw=0, dd=0, fh=None):
    return dict(plan=plan, roof=roof, floors=floors, feats=list(feats), margin=margin, skin=skin, dw=dw, dd=dd, fh=fh)


# wall treatments (override the pack's default cladding); every pack has its own set
SKINS = {
    # Neoterra
    "glass": dict(wall="light_blue_stained_glass", batten="white_concrete", frame="white_concrete", post="gray_concrete",
                  wall2="light_blue_stained_glass"),
    "concrete": dict(wall="white_concrete", batten="light_gray_concrete", frame="light_gray_concrete", post="gray_concrete",
                     wall2="white_concrete"),
    "dark": dict(wall="gray_concrete", batten="black_concrete", frame="black_concrete", post="black_concrete",
                 wall2="gray_concrete"),
    "lab": dict(wall="white_concrete", batten="cyan_terracotta", frame="cyan_concrete", post="white_concrete",
                wall2="light_blue_concrete"),
    # Hearthwood
    "brick": dict(wall="bricks", batten="bricks", frame="stone_bricks", post="stone_bricks", wall2="bricks"),
    "stonework": dict(wall="stone_bricks", batten="stone_bricks", frame="chiseled_stone_bricks", post="stone_bricks",
                      wall2="stone_bricks"),
    "redbarn": dict(wall="red_terracotta", batten="white_terracotta", frame="white_terracotta",
                    post="stripped_birch_log[axis=y]", wall2="red_terracotta"),
    "mudbrick": dict(wall="mud_bricks", batten="packed_mud", frame="dark_oak_planks", post="stripped_dark_oak_log[axis=y]",
                     wall2="mud_bricks"),
    # Cascadia
    "log": dict(wall="stripped_spruce_log[axis=y]", batten="spruce_log[axis=y]", frame="dark_oak_log[axis=y]",
                post="dark_oak_log[axis=y]", wall2="stripped_spruce_log[axis=y]"),
    "riverrock": dict(wall="cobblestone", batten="mossy_cobblestone", frame="spruce_log[axis=y]", post="spruce_log[axis=y]",
                      wall2="mossy_cobblestone"),
    "weathered": dict(wall="stripped_spruce_wood[axis=y]", batten="spruce_planks", frame="dark_oak_log[axis=y]",
                      post="dark_oak_log[axis=y]", wall2="stripped_spruce_wood[axis=y]"),
    "cedar": dict(wall="mangrove_planks", batten="stripped_mangrove_log[axis=y]", frame="dark_oak_log[axis=y]",
                  post="dark_oak_log[axis=y]", wall2="mangrove_planks"),
}

FH = {"Neoterra": 5, "Hearthwood": 4, "Cascadia": 4}
F1 = {1: 1, 2: 1, 3: 1, 4: 2, 5: 2}
F2 = {1: 1, 2: 2, 3: 2, 4: 2, 5: 3}
F3 = {1: 1, 2: 2, 3: 2, 4: 3, 5: 3}
G1 = {1: 1, 2: 1, 3: 1, 4: 1, 5: 2}          # low buildings
T4 = {1: 2, 2: 3, 3: 3, 4: 4, 5: 5}          # towers
T3 = {1: 2, 2: 2, 3: 3, 4: 3, 5: 4}

# ---------------------------------------------------------------------------------------------------------------
# NEOTERRA – the modern city: concrete, glass and steel; flat roofs, tall storeys, cubes and slabs
NEO = {
    "townhall": T("box_wide", "flat", T3, [(1, "glass_canopy"), (2, "fins"), (3, "roof_terrace"), (4, "antenna"), (5, "screen")], 6, "glass", 2, 2),
    "university": T("civic", "flat", F2, [(1, "glass_canopy"), (2, "fins"), (3, "solar_roof"), (5, "antenna")], 6, "concrete", 0, 3),
    "communitycollege": T("box_wide", "flat", F2, [(1, "glass_canopy"), (2, "light_strips"), (4, "solar_roof")], 6, "lab"),
    "school": T("longhall", "flat", F2, [(1, "glass_canopy"), (2, "solar_roof"), (3, "light_strips")], 5, "concrete", 2),
    "library": T("box", "flat", F3, [(1, "fins"), (2, "glass_cube"), (4, "roof_terrace")], 6, "glass", 3, 3),
    "hospital": T("box", "flat", T4, [(1, "glass_canopy"), (2, "light_strips"), (3, "helipad"), (4, "antenna")], 6, "lab", 2, 1),
    "cottage": T("box", "flat", G1, [(1, "glass_cube"), (3, "solar_roof")], 6, "concrete", 1, -1),
    "house": T("split", "pitched", F2, [(1, "glass_canopy"), (2, "roof_terrace"), (3, "solar_roof")], 5, "concrete"),
    "apartment": T("box", "flat", T4, [(1, "glass_canopy"), (2, "balconies"), (3, "fins"), (5, "roof_terrace")], 5, "concrete", 2, 0),
    "quadplex": T("box_wide", "flat", T3, [(1, "glass_canopy"), (2, "balconies"), (4, "solar_roof")], 5, "lab", 0, 2),
    "tavern": T("box", "flat", F2, [(1, "screen"), (2, "roof_terrace"), (3, "light_strips")], 5, "dark", 1, 2),
    "cook": T("box_wide", "flat", F1, [(1, "glass_front"), (1, "glass_canopy"), (3, "roof_terrace")], 5, "glass", 2),
    "cookery": T("box", "flat", F1, [(1, "glass_front"), (2, "light_strips")], 5, "concrete", 0, 2),
    "baker": T("box", "pitched", F1, [(1, "glass_front"), (2, "screen"), (3, "solar_roof")], 5, "lab", -1, 1),
    "builder": T("box_wide", "flat", F1, [(1, "crane"), (2, "loading_docks"), (4, "solar_roof")], 7, "dark", 3),
    "lumberjack": T("box", "pitched", F1, [(1, "glass_cube"), (2, "solar_roof")], 6, "concrete", 0, 1),
    "sawmill": T("box_wide", "industrial", F1, [(1, "loading_docks"), (2, "conveyor"), (3, "solar_roof")], 6, "dark", 2, 2),
    "stonemason": T("box_wide", "industrial", F1, [(1, "crane"), (2, "solar_roof")], 7, "concrete", 1, 3),
    "mechanic": T("box_wide", "industrial", F1, [(1, "loading_docks"), (2, "antenna"), (3, "solar_roof")], 6, "dark", 5, 1),
    "playerhouse": T("split", "flat", F2, [(1, "glass_front"), (2, "roof_terrace"), (3, "glass_cube"), (4, "solar_roof")], 6, "concrete", 3, 2),
    "deliveryman": T("box_wide", "flat", F1, [(1, "loading_docks"), (2, "screen"), (3, "antenna")], 6, "lab", 2),
    "warehouse": T("box_wide", "industrial", F1, [(1, "loading_docks"), (2, "solar_roof"), (3, "crane")], 7, "dark", 4, 2),
    "blacksmith": T("box", "industrial", F1, [(1, "cooling_tower"), (3, "light_strips")], 7, "dark", 2),
    "fletcher": T("box", "flat", F1, [(1, "glass_canopy"), (2, "fins")], 5, "concrete", 0, 2),
    "alchemist": T("box", "flat", F2, [(1, "glass_cube"), (2, "light_strips"), (4, "antenna")], 6, "lab", 1, 1),
    "dyer": T("box_wide", "flat", F1, [(1, "screen"), (2, "light_strips")], 5, "lab"),
    "glassblower": T("box", "flat", F1, [(1, "glass_cube"), (2, "fins")], 6, "glass", 2, 1),
    "concretemixer": T("box_wide", "industrial", F1, [(1, "cooling_tower"), (2, "conveyor")], 7, "concrete", 2),
    "crusher": T("box_wide", "industrial", F1, [(1, "conveyor"), (3, "antenna")], 6, "dark", 1, 3),
    "sifter": T("box", "industrial", F1, [(1, "conveyor"), (2, "solar_roof")], 6, "concrete", 2, 2),
    "smeltery": T("box_wide", "industrial", F1, [(1, "cooling_tower"), (2, "loading_docks")], 7, "dark", 3, 1),
    "stonesmeltery": T("box_wide", "industrial", F1, [(1, "cooling_tower"), (3, "light_strips")], 7, "concrete", 1, 2),
    "miner": T("box", "flat", F1, [(1, "headframe"), (2, "light_strips")], 7, "dark", 1, 1),
    "netherworker": T("box", "flat", F2, [(1, "light_strips"), (2, "antenna")], 6, "dark", 2, 2),
    "farmer": T("box_wide", "flat", F1, [(1, "solar_roof"), (2, "silo_modern")], 7, "concrete", 3),
    "cowboy": T("box_wide", "barn", F1, [(1, "silo_modern"), (3, "solar_roof")], 7, "dark", 2, 1),
    "shepherd": T("box_wide", "pitched", F1, [(1, "glass_canopy"), (2, "solar_roof")], 6, "dark", 1),
    "swineherder": T("box_wide", "flat", G1, [(1, "solar_roof")], 6, "concrete", 2, -1),
    "chickenherder": T("box", "pitched", F1, [(1, "glass_cube"), (2, "solar_roof")], 6, "concrete", 1, 1),
    "rabbithutch": T("box", "flat", G1, [(1, "glass_canopy")], 5, "lab"),
    "stable": T("box_wide", "barn", F1, [(1, "glass_canopy"), (2, "solar_roof")], 6, "dark", 3),
    "composter": T("box_wide", "flat", F1, [(1, "silo_modern"), (2, "solar_roof")], 7, "concrete", 1),
    "beekeeper": T("box", "flat", G1, [(1, "glass_cube"), (2, "solar_roof")], 6, "lab", 1),
    "florist": T("box", "flat", F1, [(1, "glass_roof"), (1, "glass_front")], 5, "glass", 2, 1),
    "plantation": T("box_wide", "flat", F1, [(1, "glass_cube"), (2, "solar_roof")], 7, "glass", 2),
    "fisherman": T("box", "flat", G1, [(1, "glass_canopy"), (2, "roof_terrace")], 6, "concrete", 1, -1),
    "guardtower": T("tower", "flat", T4, [(1, "antenna"), (2, "light_strips")], 5, "dark", 0, 0),
    "archery": T("box_wide", "flat", F1, [(1, "targets"), (2, "fins")], 6, "concrete", 2),
    "combatacademy": T("box_wide", "flat", F2, [(1, "screen"), (3, "light_strips")], 6, "dark", 3, 2),
    "enchanter": T("tower", "flat", T3, [(1, "light_strips"), (2, "antenna")], 6, "lab", 2),
    "graveyard": T("box", "flat", G1, [(1, "fins"), (2, "light_strips")], 5, "concrete", 1),
    "mysticalsite": T("box", "flat", F2, [(1, "glass_cube"), (2, "light_strips"), (4, "antenna")], 6, "glass", 2, 2),
}

# HEARTHWOOD – the cosy market town: brick, plaster and half-timber; gables and hips, compact and narrow
HEARTH = {
    "townhall": T("house_T", "hip", F3, [(1, "wall_lanterns"), (2, "portico"), (3, "gable_clock"), (4, "cupola"), (5, "shutters")], 6, "brick", -2, 3),
    "university": T("longhall_T", "hip", F2, [(1, "wall_lanterns"), (2, "portico"), (3, "cupola"), (4, "shutters")], 6, "brick", 0, 2),
    "communitycollege": T("house_L", "gable", F2, [(1, "shutters"), (2, "cupola"), (3, "bench")], 6, "brick", -1, 1),
    "school": T("house_T", "gable", F1, [(1, "cupola"), (2, "bench"), (3, "shutters")], 6, "brick", -2, 2),
    "library": T("house_L", "hip", F2, [(1, "bay_window"), (2, "wall_lanterns"), (3, "dormers")], 6, "stonework", -2, 2),
    "hospital": T("house_T", "hip", F2, [(1, "red_cross"), (2, "porch"), (3, "shutters"), (4, "bench")], 6, None, -1, 3),
    "cottage": T("house_L", "steep", F1, [(1, "chimney"), (2, "shutters"), (3, "bench")], 6, None, -3, 1),
    "playerhouse": T("house_T", "hip", F2, [(1, "porch"), (2, "bay_window"), (3, "chimney"), (4, "dormers"), (5, "shutters")], 6, "brick", -1, 3),
    "house": T("house_T", "steep", F2, [(1, "porch"), (2, "bay_window"), (3, "dormers")], 6, None, -2, 2),
    "apartment": T("box", "gable", T3, [(1, "shutters"), (2, "wall_lanterns"), (3, "dormers")], 5, "brick", -3, 3),
    "quadplex": T("house_T", "hip", F3, [(1, "porch"), (2, "shutters"), (3, "chimney")], 6, "brick", -2, 1),
    "tavern": T("house_L", "steep", F3, [(1, "hanging_sign"), (1, "chimney"), (2, "bench"), (3, "bay_window")], 6, None, -1, 2),
    "cook": T("shop", "steep", F2, [(1, "storefront"), (1, "awning"), (3, "chimney")], 6, None, -2, 2),
    "cookery": T("shop", "gable", F1, [(1, "bay_window"), (2, "chimney"), (3, "shutters")], 6, "brick", -1),
    "baker": T("shop", "steep", F2, [(1, "storefront"), (1, "awning"), (2, "chimney"), (3, "hanging_sign")], 6, None, -2, 1),
    "builder": T("house_L", "gable", F1, [(1, "awning"), (2, "wall_lanterns"), (3, "chimney")], 6, None, -1, 2),
    "lumberjack": T("house_L", "steep", F1, [(1, "shutters"), (2, "chimney")], 6, "mudbrick", -2),
    "sawmill": T("house_T", "gable", F1, [(1, "hoist"), (2, "awning")], 6, "mudbrick", -1, 2),
    "stonemason": T("house_L", "hip", F1, [(1, "stone_pile"), (2, "wall_lanterns")], 6, "stonework", -2, 1),
    "mechanic": T("house_T", "shed_roof", F1, [(1, "awning"), (2, "chimney")], 6, "brick", -1, 2),
    "deliveryman": T("shop", "gable", F2, [(1, "hanging_sign"), (2, "storefront"), (3, "wall_lanterns")], 6, None, -1, 1),
    "warehouse": T("house_T", "gable", F2, [(1, "hoist"), (2, "shutters")], 6, "brick", -2, 3),
    "blacksmith": T("house_L", "gable", F1, [(1, "forge_chimney"), (2, "hanging_sign"), (3, "awning")], 6, "stonework", -2, 1),
    "fletcher": T("shop", "steep", F1, [(1, "hanging_sign"), (2, "shutters")], 6, None, -2),
    "alchemist": T("shop", "steep", F2, [(1, "bay_window"), (1, "hanging_sign"), (3, "sunroom")], 6, None, -2, 2),
    "dyer": T("house_L", "gable", F1, [(1, "drying_line"), (2, "shutters")], 6, "mudbrick", -1),
    "glassblower": T("house_L", "gable", F1, [(1, "kiln"), (2, "bay_window")], 6, "brick", -2, 1),
    "concretemixer": T("house_T", "shed_roof", F1, [(1, "kiln"), (2, "hoist")], 6, "brick", -1, 2),
    "crusher": T("house_L", "shed_roof", F1, [(1, "hoist"), (2, "stone_pile")], 6, "stonework", -1, 1),
    "sifter": T("house_L", "gable", F1, [(1, "stone_pile"), (2, "awning")], 6, "mudbrick", -2),
    "smeltery": T("house_T", "gable", F1, [(1, "smokestacks"), (2, "hoist")], 6, "brick", -1, 3),
    "stonesmeltery": T("house_L", "hip", F1, [(1, "kiln"), (2, "smokestacks")], 6, "brick", -2, 2),
    "miner": T("house_L", "gable", F1, [(1, "stone_pile"), (2, "chimney")], 6, "stonework", -2, 1),
    "netherworker": T("house_T", "steep", F2, [(1, "forge_chimney"), (2, "wall_lanterns")], 6, "stonework", -1, 1),
    "farmer": T("house_L", "barn", F1, [(1, "barn_doors"), (2, "dovecote"), (3, "chimney")], 6, "redbarn", -1, 2),
    "cowboy": T("house_T", "barn", F1, [(1, "barn_doors"), (2, "dovecote")], 6, "redbarn", -1, 1),
    "shepherd": T("house_L", "steep", F1, [(1, "barn_doors"), (2, "shutters")], 6, "redbarn", -2),
    "swineherder": T("house_L", "gable", G1, [(1, "barn_doors")], 6, "redbarn", -2, 1),
    "chickenherder": T("shop", "steep", F1, [(1, "dovecote"), (2, "bench")], 6, "redbarn", -2),
    "rabbithutch": T("house_L", "gable", G1, [(1, "shutters")], 6, "redbarn", -3),
    "stable": T("house_T", "barn", F1, [(1, "barn_doors"), (2, "cupola")], 6, "redbarn", -1, 2),
    "composter": T("house_L", "shed_roof", F1, [(1, "compost_bins")], 6, "mudbrick", -2),
    "beekeeper": T("house_L", "steep", F1, [(1, "bench"), (2, "chimney")], 6, None, -3),
    "florist": T("shop", "steep", F1, [(1, "storefront"), (1, "awning"), (2, "sunroom")], 6, None, -2, 1),
    "plantation": T("house_T", "gable", F1, [(1, "sunroom"), (2, "shutters")], 6, "mudbrick", -1, 1),
    "fisherman": T("house_L", "steep", F1, [(1, "nets"), (2, "bench")], 6, None, -3),
    "guardtower": T("tower", "battlement", T3, [(1, "battlements"), (2, "wall_lanterns")], 5, "stonework", 1, 1),
    "archery": T("house_L", "gable", F1, [(1, "hanging_sign"), (2, "wall_lanterns")], 6, "stonework", -1),
    "combatacademy": T("house_T", "hip", F1, [(1, "battlements_low"), (2, "portico")], 6, "stonework", -1, 2),
    "enchanter": T("house_L", "steep", F2, [(1, "mage_tower")], 6, "stonework", -2, 1),
    "graveyard": T("house_L", "steep", F1, [(1, "steeple"), (2, "wall_lanterns")], 6, "stonework", -2),
    "mysticalsite": T("house_T", "hip", F1, [(1, "portico"), (2, "dome")], 6, "stonework", -1, 1),
}

# CASCADIA – the Pacific Northwest backcountry: logs, cedar, river rock and moss; long low lodges, steep roofs
CASC = {
    "townhall": T("lodge_L", "steep", F2, [(1, "log_porch"), (2, "stone_chimney"), (3, "lookout"), (4, "moss_ridge")], 6, "log", 4, -1),
    "university": T("longhall", "steep", F2, [(1, "log_porch"), (2, "stone_chimney"), (3, "lantern_posts")], 6, "cedar", 5),
    "communitycollege": T("lodge_L", "pitched", F1, [(1, "covered_entry"), (2, "moss_ridge"), (3, "lantern_posts")], 6, "weathered", 3),
    "school": T("aframe", "steep", F1, [(1, "log_porch"), (2, "lantern_posts")], 6, "cedar", 3, -1),
    "library": T("lodge_L", "steep", F1, [(1, "stone_chimney"), (2, "log_porch"), (3, "moss_ridge")], 6, "riverrock", 4),
    "hospital": T("longhall", "pitched", F1, [(1, "covered_entry"), (2, "stone_chimney"), (3, "rain_barrels")], 6, "weathered", 5, -1),
    "cottage": T("aframe", "steep", G1, [(1, "firewood"), (2, "stone_chimney")], 6, "log", 2),
    "playerhouse": T("lodge_L", "steep", F2, [(1, "log_porch"), (2, "stone_chimney"), (3, "firewood"), (4, "moss_ridge")], 6, "log", 5, -1),
    "house": T("lodge_L", "pitched", F1, [(1, "log_porch"), (2, "firewood"), (3, "stone_chimney")], 6, "cedar", 3),
    "apartment": T("longhall_T", "pitched", F2, [(1, "log_porch"), (2, "deck"), (3, "moss_ridge")], 6, "weathered", 4, -1),
    "quadplex": T("longhall", "steep", F2, [(1, "log_porch"), (2, "firewood")], 6, "log", 5),
    "tavern": T("lodge_L", "steep", F2, [(1, "log_porch"), (1, "stone_chimney"), (2, "lantern_posts"), (3, "rain_barrels")], 6, "log", 3),
    "cook": T("longhall", "pitched", F1, [(1, "log_porch"), (2, "stone_chimney"), (3, "firewood")], 6, "cedar", 3, -1),
    "cookery": T("lodge_L", "pitched", F1, [(1, "stone_chimney"), (2, "rain_barrels")], 6, "riverrock", 2),
    "baker": T("longhall", "steep", F1, [(1, "stone_chimney"), (2, "firewood"), (3, "lantern_posts")], 6, "riverrock", 3),
    "builder": T("barn", "steep", F1, [(1, "log_piles"), (2, "lantern_posts")], 6, "weathered", 4),
    "lumberjack": T("aframe", "steep", F1, [(1, "log_piles"), (2, "firewood"), (3, "stone_chimney")], 6, "log", 2),
    "sawmill": T("barn", "pitched", F1, [(1, "water_wheel"), (2, "log_piles")], 6, "weathered", 5, -1),
    "stonemason": T("longhall", "pitched", F1, [(1, "rock_pile"), (2, "stone_chimney")], 6, "riverrock", 4),
    "mechanic": T("barn", "pitched", F1, [(1, "rain_barrels"), (2, "lantern_posts")], 6, "weathered", 4),
    "deliveryman": T("longhall", "pitched", F1, [(1, "covered_entry"), (2, "lantern_posts")], 6, "cedar", 4),
    "warehouse": T("barn", "pitched", F1, [(1, "covered_entry"), (2, "log_piles")], 6, "weathered", 6),
    "blacksmith": T("lodge_L", "pitched", F1, [(1, "stone_chimney"), (2, "rock_pile")], 6, "riverrock", 2),
    "fletcher": T("longhall", "steep", F1, [(1, "firewood"), (2, "lantern_posts")], 6, "cedar", 3),
    "alchemist": T("aframe", "steep", F1, [(1, "rain_barrels"), (2, "moss_ridge")], 6, "cedar", 2),
    "dyer": T("longhall", "pitched", F1, [(1, "rain_barrels"), (2, "log_porch")], 6, "weathered", 3),
    "glassblower": T("lodge_L", "pitched", F1, [(1, "stone_chimney"), (2, "rain_barrels")], 6, "riverrock", 3),
    "concretemixer": T("barn", "pitched", F1, [(1, "rock_pile"), (2, "water_wheel")], 6, "riverrock", 4),
    "crusher": T("barn", "pitched", F1, [(1, "water_wheel"), (2, "rock_pile")], 6, "weathered", 4),
    "sifter": T("longhall", "pitched", F1, [(1, "rock_pile"), (2, "rain_barrels")], 6, "weathered", 3),
    "smeltery": T("lodge_L", "pitched", F1, [(1, "stone_chimney"), (2, "rock_pile")], 6, "riverrock", 4),
    "stonesmeltery": T("barn", "steep", F1, [(1, "stone_chimney"), (2, "rock_pile")], 6, "riverrock", 3),
    "miner": T("longhall", "pitched", F1, [(1, "mine_portal"), (2, "lantern_posts")], 6, "log", 3),
    "netherworker": T("lodge_L", "steep", F1, [(1, "stone_chimney"), (2, "lantern_posts")], 6, "riverrock", 2),
    "farmer": T("barn", "barn", F1, [(1, "hay_loft"), (2, "rain_barrels"), (3, "moss_ridge")], 6, "weathered", 5),
    "cowboy": T("barn", "barn", F1, [(1, "hay_loft"), (2, "log_piles")], 6, "weathered", 6),
    "shepherd": T("longhall", "steep", F1, [(1, "hay_loft"), (2, "moss_ridge")], 6, "log", 4),
    "swineherder": T("longhall", "pitched", G1, [(1, "rain_barrels")], 6, "weathered", 4, -1),
    "chickenherder": T("aframe", "steep", F1, [(1, "firewood")], 6, "cedar", 2),
    "rabbithutch": T("aframe", "steep", G1, [(1, "moss_ridge")], 6, "log", 2, -1),
    "stable": T("barn", "barn", F1, [(1, "hay_loft"), (2, "lantern_posts")], 6, "log", 6),
    "composter": T("longhall", "pitched", F1, [(1, "firewood"), (2, "rain_barrels")], 6, "weathered", 3),
    "beekeeper": T("aframe", "steep", G1, [(1, "log_porch"), (2, "moss_ridge")], 6, "cedar", 2),
    "florist": T("lodge_L", "pitched", F1, [(1, "log_porch"), (2, "rain_barrels")], 6, "cedar", 2),
    "plantation": T("longhall", "pitched", F1, [(1, "covered_entry"), (2, "rain_barrels")], 6, "cedar", 4),
    "fisherman": T("aframe", "steep", G1, [(1, "deck"), (2, "lantern_posts")], 6, "weathered", 2),
    "guardtower": T("tower", "steep", T3, [(1, "lookout"), (2, "lantern_posts")], 6, "log", 2, 2),
    "archery": T("longhall", "pitched", F1, [(1, "lookout"), (2, "lantern_posts")], 6, "log", 4),
    "combatacademy": T("barn", "steep", F1, [(1, "log_porch"), (2, "lantern_posts")], 6, "log", 5),
    "enchanter": T("aframe", "steep", F2, [(1, "moss_ridge"), (2, "lantern_posts")], 6, "riverrock", 3),
    "graveyard": T("aframe", "steep", G1, [(1, "lantern_posts"), (2, "moss_ridge")], 6, "weathered", 2),
    "mysticalsite": T("lodge_L", "steep", F1, [(1, "lantern_posts"), (2, "moss_ridge"), (3, "stone_chimney")], 6, "riverrock", 3),
}

SPECS = {"Neoterra": NEO, "Hearthwood": HEARTH, "Cascadia": CASC}
SPEC = HEARTH                                        # kept for older callers


# final per-pack material vocabulary: (old name or family prefix, new) – applied to every non-functional block
REMAP = {
    "Cascadia": [("dark_oak_", "mangrove_"), ("stripped_dark_oak_", "stripped_mangrove_"), ("oak_", "spruce_"),
                 ("stripped_oak_", "stripped_spruce_"), ("birch_", "spruce_"), ("stripped_birch_", "stripped_spruce_"),
                 ("stone_bricks", "mossy_stone_bricks"), ("stone_brick_", "mossy_stone_brick_"), ("glass_pane", "glass"),
                 ("white_concrete", "calcite"), ("bricks", "mud_bricks"), ("brick_", "mud_brick_"),
                 ("polished_andesite", "tuff"), ("smooth_stone", "tuff"), ("white_terracotta", "calcite")],
    "Hearthwood": [("spruce_", "oak_"), ("stripped_spruce_", "stripped_oak_"), ("birch_", "oak_"),
                   ("stripped_birch_", "stripped_oak_"), ("mangrove_", "dark_oak_"), ("cobblestone", "stone_bricks"),
                   ("mossy_cobblestone", "mossy_stone_bricks"), ("cobblestone_", "stone_brick_"), ("andesite", "stone"),
                   ("tuff", "stone"), ("campfire", "decorated_pot"), ("hay_block", "pumpkin"), ("white_concrete", "white_terracotta"),
                   ("glass", "white_stained_glass"), ("gravel", "packed_mud"), ("coarse_dirt", "packed_mud"),
                   ("calcite", "white_terracotta")],
    "Neoterra": [("oak_", "birch_"), ("dark_oak_", "birch_"), ("spruce_", "birch_"), ("mangrove_", "birch_"),
                 ("stripped_oak_", "stripped_birch_"), ("stripped_spruce_", "stripped_birch_"),
                 ("stripped_dark_oak_", "stripped_birch_"), ("glass_pane", "light_blue_stained_glass_pane"),
                 ("cobblestone", "gray_concrete"), ("mossy_cobblestone", "gray_concrete"), ("stone_bricks", "light_gray_concrete"),
                 ("bricks", "gray_concrete"), ("campfire", "soul_campfire"), ("hay_block", "white_wool"),
                 ("gravel", "light_gray_concrete_powder")],
}
FUNCTIONAL = ("blockhut", "rack", "crafting_table", "furnace", "smoker", "barrel", "anvil", "lectern", "bookshelf",
              "stonecutter", "grindstone", "loom", "cartography", "fletching", "smithing", "brewing", "enchanting",
              "cauldron", "composter", "_bed", "chest", "jukebox", "bell", "beehive", "bee_nest", "target", "hopper",
              "substitution", "field", "grave", "scarecrow", "portal", "obsidian", "farmland", "water", "lava", "rail",
              "ladder", "_door", "flower_pot", "potted_", "carpet", "lantern")
NO_PROPS = {"glass", "calcite", "mossy_stone_bricks", "mud_bricks", "tuff", "stone", "stone_bricks", "mossy_stone_bricks",
            "white_terracotta", "white_stained_glass", "pumpkin", "white_wool", "gray_concrete", "light_gray_concrete",
            "packed_mud", "light_gray_concrete_powder", "decorated_pot"}


def remap(style, state):
    ns, _, rest = state.partition(":")
    if ns != "minecraft":
        return state
    name, br, props = rest.partition("[")
    if any(f in name for f in FUNCTIONAL):
        return state
    new = name
    for old, rep in REMAP[style]:
        if old.endswith("_"):
            if new.startswith(old) and not (old == "oak_" and new.startswith("dark_oak_")):
                cand = rep + new[len(old):]
                new = cand
                break
        elif new == old or (old in ("bricks",) and new == "bricks"):
            new = rep
            break
    if new == name:
        return state
    if new == "decorated_pot":
        return "minecraft:decorated_pot[cracked=false,facing=north,waterlogged=false]"
    if new in NO_PROPS or new.endswith("_concrete") or new.endswith("_terracotta"):
        return "minecraft:" + new
    if name in ("hay_block",):
        return "minecraft:" + new
    return "minecraft:" + new + (br + props if br else "")


def spec(style, base):
    return SPECS[style].get(base)


def roof_form(style, kind):
    return ROOFMAP[style][kind]


# ------------------------------------------------------------------------------------------------ helpers
class _Ctx:
    def __init__(self, a):
        self.a = a
        self.bp = a.bp
        self.x1, self.x2, self.z1, self.z2, self.nf, _ = a.vols[0]
        self.gy = a.gy
        self.M = a.M
        self.style = a.style
        self.L = a.L
        self.wood = WOOD[a.style]
        self.dx = a.door_x
        self.cx = (self.x1 + self.x2) // 2
        self.cz = (self.z1 + self.z2) // 2
        self.ytop = a.floor_y(self.nf)

    def S(self, x, y, z, s, force=False):
        self.a.S(x, y, z, s, force=force)

    def get(self, x, y, z):
        return self.bp.get(x, y, z) if self.bp.inside(x, y, z) else AIR

    def free(self, x, y, z):
        return self.bp.inside(x, y, z) and self.bp.get(x, y, z) == AIR and (x, y, z) not in self.a.locked

    def top(self, x, z):
        for y in range(self.bp.sy - 1, -1, -1):
            if self.get(x, y, z) != AIR:
                return y
        return 0

    def stair(self, mat, facing, half="bottom"):
        return f"{mat}_stairs[facing={facing},half={half},shape=straight,waterlogged=false]"

    def fence(self, mat=None):
        return f"{mat or self.wood}_fence[east=false,north=false,south=false,waterlogged=false,west=false]"

    def flag_pole(self, x, z, h):
        for y in range(self.gy + 1, self.gy + h):
            self.S(x, y, z, self.fence())
        cols = FLAG[self.style]
        for i, dx in enumerate((1, 2, 3)):
            for dy in (0, 1):
                self.S(x + dx, self.gy + h - 2 + dy, z, cols[(i + dy) % 2])
        self.S(x, self.gy + h, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")

    def wall_mat(self):
        return self.M["wall"]


# ------------------------------------------------------------------------------------------------ features
def f_flagpole(c):
    x = c.x1 - 3 if c.x1 - 3 >= 1 else c.x2 + 2
    c.flag_pole(x, c.z1 - 3, 9 + c.L)


def f_portico(c):
    """Columns, entablature and (except Neoterra) a triangular pediment in front of the door."""
    zf = c.z1 - 3
    width = min(5, (c.x2 - c.x1) // 2 - 1)
    xs = [c.dx + o for o in (-width, -2, 2, width) if c.x1 - 1 <= c.dx + o <= c.x2 + 1]
    col = c.M["post"] if c.style != "Neoterra" else ("quartz_pillar[axis=y]" if c.L >= 4 else "white_concrete")
    top = c.gy + 4
    for x in range(c.dx - width - 1, c.dx + width + 2):
        for z in range(zf, c.z1):
            c.S(x, c.gy, z, STONE[c.style] if c.style != "Neoterra" else c.M["deck"], force=True)
    for x in xs:
        for y in range(c.gy + 1, top):
            c.S(x, y, zf, col)
    for x in range(c.dx - width - 1, c.dx + width + 2):
        for z in range(zf, c.z1):
            c.S(x, top, z, c.M["ridge"] if c.style != "Neoterra" else "smooth_quartz_slab[type=bottom,waterlogged=false]"
                if c.L >= 4 else "smooth_stone_slab[type=bottom,waterlogged=false]")
    if c.style != "Neoterra":
        roof = c.a.M["roof5"] if c.a.top else c.a.M["roof"]
        for k in range(width + 2):
            y = top + 1 + k
            xa, xb = c.dx - width - 1 + k, c.dx + width + 1 - k
            if xa > xb:
                break
            c.S(xa, y, zf, c.stair(roof, "east"))
            c.S(xb, y, zf, c.stair(roof, "west"))
            for x in range(xa + 1, xb):
                c.S(x, y, zf, c.M["wall"])
            for z in range(zf + 1, c.z1):
                for x in range(xa, xb + 1):
                    c.S(x, y, z, c.M["ridge"])


def f_clock_tower(c):
    """Square tower rising from the middle of the roof with clock faces, belfry and spire."""
    r = 2 if (c.x2 - c.x1) >= 10 and (c.z2 - c.z1) >= 8 else 1
    xs, zs = range(c.cx - r, c.cx + r + 1), range(c.cz - r, c.cz + r + 1)
    base = c.ytop + 1
    ridge = max(c.top(x, z) for x in xs for z in zs)
    clock = ridge + 2
    belfry = clock + 3
    for y in range(base, belfry + 3):
        for x in xs:
            for z in zs:
                edge = x in (xs[0], xs[-1]) or z in (zs[0], zs[-1])
                corner = x in (xs[0], xs[-1]) and z in (zs[0], zs[-1])
                if y >= belfry:
                    s = c.M["post"] if corner else AIR
                else:
                    s = (c.M["post"] if corner else c.M["wall"]) if edge else AIR
                c.S(x, y, z, s, force=True)
    for d in range(-min(r, 1), min(r, 1) + 1):              # faces on all four sides
        for dy in (-1, 0, 1) if r == 2 else (0,):
            for x, z in ((c.cx + d, zs[0]), (c.cx + d, zs[-1]), (xs[0], c.cz + d), (xs[-1], c.cz + d)):
                c.S(x, clock + dy, z, FACE[c.style], force=True)
    for x, z in ((c.cx, zs[0]), (c.cx, zs[-1]), (xs[0], c.cz), (xs[-1], c.cz)):
        c.S(x, clock, z, "black_concrete" if c.style == "Neoterra" else "dark_oak_planks", force=True)
    for x in xs:
        for z in zs:
            c.S(x, belfry - 1, z, c.M["ridge"], force=True)
            c.S(x, belfry + 3, z, c.M["ridge"], force=True)
    c.S(c.cx, belfry + 2, c.cz, "bell[attachment=ceiling,facing=north,powered=false]", force=True)
    y = belfry + 4
    if c.style == "Neoterra":
        for k in range(4):
            c.S(c.cx, y + k, c.cz, "sea_lantern" if k == 0 else "end_rod[facing=up]", force=True)
        return
    roof = c.a.M["roof5"] if c.a.top else c.a.M["roof"]
    rr = r + 1
    while rr >= 0:
        for x in range(c.cx - rr, c.cx + rr + 1):
            for z in range(c.cz - rr, c.cz + rr + 1):
                ring = abs(x - c.cx) == rr or abs(z - c.cz) == rr
                if not ring and rr:
                    continue
                if rr == 0:
                    c.S(x, y, z, c.M["ridge"], force=True)
                elif x == c.cx - rr:
                    c.S(x, y, z, c.stair(roof, "east"), force=True)
                elif x == c.cx + rr:
                    c.S(x, y, z, c.stair(roof, "west"), force=True)
                elif z == c.cz - rr:
                    c.S(x, y, z, c.stair(roof, "south"), force=True)
                else:
                    c.S(x, y, z, c.stair(roof, "north"), force=True)
        rr -= 1
        y += 1
    c.S(c.cx, y, c.cz, "lightning_rod[facing=up,powered=false,waterlogged=false]", force=True)


def f_dome(c):
    r = max(2, min(c.x2 - c.x1, c.z2 - c.z1) // 2 - 2)
    if r < 2:
        return
    base = max(c.top(x, z) for x in range(c.cx - r, c.cx + r + 1) for z in range(c.cz - r, c.cz + r + 1)) + 1
    mat = {"Neoterra": "white_concrete", "Hearthwood": "waxed_cut_copper", "Cascadia": "waxed_weathered_cut_copper"}[c.style]
    if c.style == "Neoterra" and c.L >= 4:
        mat = "light_blue_stained_glass"
    for x in range(c.cx - r, c.cx + r + 1):                 # drum
        for z in range(c.cz - r, c.cz + r + 1):
            d = math.hypot(x - c.cx, z - c.cz)
            if r - 0.5 < d <= r + 0.5:
                c.S(x, base, z, c.M["wall"], force=True)
    for x in range(c.cx - r, c.cx + r + 1):
        for z in range(c.cz - r, c.cz + r + 1):
            for y in range(base + 1, base + r + 2):
                d = math.sqrt((x - c.cx) ** 2 + (z - c.cz) ** 2 + (y - base - 1) ** 2)
                if r - 0.6 < d <= r + 0.4:
                    c.S(x, y, z, mat, force=True)
    c.S(c.cx, base + r + 2, c.cz, "lantern[hanging=false,waterlogged=false]", force=True)


def f_red_cross(c):
    if c.nf >= 2:
        y0, z = c.a.floor_y(1) + 1, c.z1
    else:
        y0, z = c.ytop + 1, c.z1
    for dy in range(3):
        c.S(c.dx, y0 + dy, z, "red_concrete", force=True)
    c.S(c.dx - 1, y0 + 1, z, "red_concrete", force=True)
    c.S(c.dx + 1, y0 + 1, z, "red_concrete", force=True)
    if c.nf >= 2:                                         # white backing
        for x in range(c.dx - 2, c.dx + 3):
            for dy in range(-1, 4):
                if c.get(x, y0 + dy, z) not in ("minecraft:red_concrete",):
                    c.S(x, y0 + dy, z, "white_concrete", force=True)


def f_helipad(c):
    if c.a.vols[0][5] != "flat":
        return
    y = c.ytop
    for x in range(c.cx - 2, c.cx + 3):
        for z in range(c.cz - 2, c.cz + 3):
            c.S(x, y, z, "white_concrete", force=True)
    for z in range(c.cz - 2, c.cz + 3):
        c.S(c.cx - 1, y, z, "yellow_concrete", force=True)
        c.S(c.cx + 1, y, z, "yellow_concrete", force=True)
    c.S(c.cx, y, c.cz, "yellow_concrete", force=True)


def f_entry_canopy(c):
    for x in range(c.dx - 2, c.dx + 3):
        for z in range(c.z1 - 2, c.z1):
            c.S(x, c.gy + 3, z, f"{'smooth_stone' if c.style == 'Neoterra' else c.wood}_slab[type=top,waterlogged=false]")
    for x in (c.dx - 2, c.dx + 2):
        for y in range(c.gy + 1, c.gy + 3):
            c.S(x, y, c.z1 - 2, c.fence())


def f_balconies(c):
    for f in range(1, c.nf):
        y = c.a.floor_y(f)
        for x0 in range(c.x1 + 2, c.x2 - 2, 5):
            for x in range(x0, x0 + 3):
                if x > c.x2 - 1:
                    continue
                for z in (c.z1 - 1, c.z1 - 2):
                    c.S(x, y, z, c.M["deck"] if c.style != "Neoterra" else "smooth_stone")
                c.S(x, y + 1, c.z1 - 2, c.fence() if c.style != "Neoterra" else "glass_pane")
            c.S(x0, y + 1, c.z1 - 1, c.fence() if c.style != "Neoterra" else "glass_pane")
            c.S(x0 + 2, y + 1, c.z1 - 1, c.fence() if c.style != "Neoterra" else "glass_pane")


def f_storefront(c):
    acc = c.M["accent"][0]
    for x in range(c.x1 + 1, c.x2):
        if abs(x - c.dx) <= 0:
            continue
        if (x, c.gy + 1, c.z1) in c.a.locked:
            continue
        for y in (c.gy + 1, c.gy + 2):
            c.S(x, y, c.z1, c.M["glass"])
        c.S(x, c.gy + 3, c.z1, acc)


def f_hanging_sign(c):
    x = c.dx + 2 if c.dx + 2 < c.x2 else c.dx - 2
    c.S(x, c.gy + 3, c.z1 - 1, c.fence())
    c.S(x, c.gy + 2, c.z1 - 1, f"{c.wood}_hanging_sign[attached=false,rotation=0,waterlogged=false]")


def f_terrace(c):
    for side in (-1, 1):
        tx = c.dx + side * 4
        if not (1 <= tx - 1 and tx + 1 < c.bp.sx - 1):
            continue
        z = c.z1 - 3
        c.S(tx, c.gy + 1, z, c.fence())
        c.S(tx, c.gy + 2, z, "white_carpet" if c.style != "Cascadia" else "green_carpet")
        c.S(tx - 1, c.gy + 1, z, c.stair(c.wood, "west"))
        c.S(tx + 1, c.gy + 1, z, c.stair(c.wood, "east"))


def f_chimney(c):
    c.a.extra("brick_chimney" if c.style == "Hearthwood" else "stone_chimney")


def f_forge_chimney(c):
    x, z = c.x2 + 1, c.z2 - 2
    top = c.ytop + 9
    for y in range(c.gy + 1, top):
        for dx in (0, 1):
            for dz in (0, 1):
                c.S(x + dx, y, z + dz, STONE[c.style] if y > c.gy + 3 else "cobblestone")
    c.S(x, top, z, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")


def f_smokestacks(c):
    n = 1 + (c.L >= 3) + (c.L >= 5)
    xs = [c.x1 + 2 + i * 4 for i in range(n) if c.x1 + 2 + i * 4 < c.x2]
    z = c.z2 + 1
    mat = {"Cascadia": "stone_bricks", "Hearthwood": "bricks", "Neoterra": "light_gray_concrete"}[c.style]
    for i, x in enumerate(xs):
        top = c.ytop + 10 + 2 * i
        for y in range(c.gy + 1, top):
            c.S(x, y, z, mat if (y // 4) % 3 else ("red_concrete" if c.style == "Neoterra" else mat))
        c.S(x, top, z, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")


def f_loading_docks(c):
    n = 1 + (c.L >= 3)
    spots = [x for x in range(c.x1 + 2, c.x2 - 2, 5) if abs(x + 1 - c.dx) > 2][:n]
    for x0 in spots:
        for x in range(x0, x0 + 3):
            for y in (c.gy + 1, c.gy + 2):
                c.S(x, y, c.z1, AIR)
            c.S(x, c.gy + 3, c.z1, "yellow_concrete" if c.style == "Neoterra" else c.M["post"].replace("axis=y", "axis=x"))
            for z in (c.z1 - 1, c.z1 - 2):
                c.S(x, c.gy, z, "smooth_stone")
                c.S(x, c.gy + 4, z, f"{'smooth_stone' if c.style == 'Neoterra' else c.wood}_slab[type=bottom,waterlogged=false]")


def f_crane(c):
    mx, mz = c.x2 + 3, c.z1 + 1
    H = c.ytop + 8
    mast = "yellow_concrete" if c.style == "Neoterra" else c.M["post"]
    for y in range(c.gy + 1, H + 1):
        c.S(mx, y, mz, mast)
    jib = "yellow_concrete" if c.style == "Neoterra" else c.M["post"].replace("axis=y", "axis=x")
    for x in range(mx - 9, mx + 3):
        c.S(x, H + 1, mz, jib)
    c.S(mx + 2, H, mz, "iron_block" if c.style == "Neoterra" else "cobblestone")
    hx = mx - 7
    for y in range(H - 3, H + 1):
        c.S(hx, y, mz, "chain[axis=y,waterlogged=false]")
    c.S(hx, H - 4, mz, "iron_block" if c.style == "Neoterra" else f"{c.wood}_planks")


def f_timber_stack(c):
    x0, z0 = c.x1 - 4, c.z1
    for i in range(3):
        for x in range(x0 + i // 2, x0 + 3 - (i + 1) // 2):
            for z in range(z0, z0 + 4):
                c.S(x, c.gy + 1 + i, z, f"stripped_{c.wood}_log[axis=z]" if c.style != "Neoterra" else "birch_log[axis=z]")


def f_log_piles(c):
    f_timber_stack(c)
    if c.L >= 3:
        x0, z0 = c.x1 - 4, c.z1 + 5
        for i in range(2):
            for x in range(x0, x0 + 3):
                for z in range(z0, z0 + 3):
                    if i == 0 or (x == x0 + 1):
                        c.S(x, c.gy + 1 + i, z, f"{c.wood}_log[axis=z]")


def f_stone_pile(c):
    x0, z0 = c.x1 - 4, c.z1
    mats = ["stone", "cobblestone", "stone_bricks", "andesite"]
    for x in range(x0, x0 + 3):
        for z in range(z0, z0 + 3):
            hgt = 1 + ((x + z) % 2)
            for y in range(c.gy + 1, c.gy + 1 + hgt):
                c.S(x, y, z, mats[(x * 3 + z + y) % len(mats)])


def f_barn_doors(c):
    """Big X-braced barn doors on the front and a hay-loft hatch above."""
    beam = f"stripped_{c.wood}_log[axis=x]" if c.style != "Neoterra" else "white_concrete"
    plank = f"{'red' if c.style == 'Cascadia' else 'brown' if c.style == 'Hearthwood' else 'light_gray'}_terracotta"
    for x in range(c.dx - 2, c.dx + 3):
        for y in range(c.gy + 1, c.gy + 4):
            if (x, y, c.z1) in c.a.locked or x == c.dx and y < c.gy + 3:
                continue
            diag = abs(x - c.dx) == (y - c.gy - 1) or abs(x - c.dx) == 2 and y == c.gy + 3
            c.S(x, y, c.z1, beam if diag or y == c.gy + 3 else plank)
    loft = c.ytop + 2
    if c.get(c.dx, loft, c.z1) != AIR:
        c.S(c.dx, loft, c.z1, f"{c.wood}_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]")
    for x in (c.dx - 4, c.dx + 4):
        if c.x1 - 3 <= x <= c.x2 + 3:
            c.S(x, c.gy + 1, c.z1 - 2, "hay_block[axis=y]")


def f_battlements(c):
    y = c.ytop + 1
    for x in range(c.x1, c.x2 + 1):
        for z in range(c.z1, c.z2 + 1):
            if x in (c.x1, c.x2) or z in (c.z1, c.z2):
                c.S(x, y, z, STONE[c.style], force=True)
                if (x + z) % 2 == 0:
                    c.S(x, y + 1, z, STONE[c.style], force=True)
    for y2 in range(y, y + 5):
        c.S(c.cx, y2, c.cz, c.fence(), force=True)
    cols = FLAG[c.style]
    for i in (1, 2, 3):
        c.S(c.cx + i, y + 3, c.cz, cols[i % 2], force=True)


def f_battlements_low(c):
    for x in range(c.x1, c.x2 + 1, 2):
        c.S(x, c.ytop, c.z1 - 1, STONE[c.style])
        c.S(x, c.ytop + 1, c.z1 - 1, STONE[c.style])


def f_targets(c):
    for z in range(c.z1, c.z2, 3):
        x = c.x2 + 3
        c.S(x, c.gy + 1, z, "hay_block[axis=y]")
        c.S(x, c.gy + 2, z, "target[power=0]")


def f_vats(c):
    for i, x in enumerate(range(c.x1 - 4, c.x1 - 1)):
        c.S(x, c.gy + 1, c.z1 + 1, "water_cauldron[level=3]")
        c.S(x, c.gy + 1, c.z1 + 3, "water_cauldron[level=3]")


def f_drying_line(c):
    xa, xb, z = c.x1 - 4, c.x1 - 1, c.z1 + 6
    for x in (xa, xb):
        for y in range(c.gy + 1, c.gy + 5):
            c.S(x, y, z, c.fence())
    cols = ["red_wool", "blue_wool", "yellow_wool", "green_wool", "purple_wool"]
    for i, x in enumerate(range(xa, xb + 1)):
        c.S(x, c.gy + 4, z, c.fence())
        if xa < x < xb:
            c.S(x, c.gy + 3, z, cols[i % len(cols)])


def f_kiln(c):
    """Bottle kiln: round brick tower that narrows to a chimney."""
    kx, kz = c.x1 - 4, c.cz
    mat = "bricks" if c.style != "Neoterra" else "light_gray_concrete"
    H = c.ytop + 6
    for y in range(c.gy + 1, H + 1):
        r = 2.4 if y < c.gy + (H - c.gy) * 0.6 else 1.4 if y < H - 1 else 0.6
        for x in range(kx - 3, kx + 4):
            for z in range(kz - 3, kz + 4):
                d = math.hypot(x - kx, z - kz)
                if r - 1 < d <= r:
                    c.S(x, y, z, mat)
    c.S(kx, H, kz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")


def f_headframe(c):
    hx, hz = c.x1 - 4, c.z1 + 1
    H = c.ytop + 7
    leg = c.M["post"] if c.style != "Neoterra" else "gray_concrete"
    for y in range(c.gy + 1, H + 1):
        c.S(hx, y, hz, leg)
        c.S(hx, y, hz + 3, leg)
    for y in range(c.gy + 3, H, 3):
        for z in range(hz + 1, hz + 3):
            c.S(hx, y, z, f"{c.wood}_planks" if c.style != "Neoterra" else "iron_bars")
    for z in range(hz, hz + 4):
        c.S(hx, H + 1, z, f"{c.wood}_planks" if c.style != "Neoterra" else "gray_concrete")
    wheel = "iron_bars" if c.style == "Neoterra" else f"{c.wood}_fence"
    for dy in range(2, 5):
        c.S(hx, H + dy, hz, leg)
        c.S(hx, H + dy, hz + 3, leg)
    for z in range(hz, hz + 4):
        c.S(hx, H + 5, z, f"{c.wood}_planks" if c.style != "Neoterra" else "gray_concrete")
    c.S(hx, H + 3, hz + 1, wheel)
    c.S(hx, H + 3, hz + 2, wheel)


def f_compost_bins(c):
    for x in range(c.x1 - 4, c.x1 - 1):
        for z in (c.z1, c.z1 + 2):
            c.S(x, c.gy + 1, z, "composter[level=4]")


def f_glass_roof(c):
    for x in range(c.x1 - 1, c.x2 + 2):
        for z in range(c.z1 - 1, c.z2 + 2):
            for y in range(c.ytop + 1, c.bp.sy):
                s = c.get(x, y, z)
                if s != AIR and ("stairs" in s or "slab" in s or s.endswith("_planks") or s == "minecraft:" + c.M["ridge"]):
                    c.S(x, y, z, "glass", force=True)


def f_flower_boxes(c):
    for x in range(c.x1 + 1, c.x2):
        if abs(x - c.dx) > 1 and (x, c.gy + 1, c.z1 - 1) not in c.a.locked:
            c.S(x, c.gy + 1, c.z1 - 1, "potted_red_tulip" if x % 2 else "potted_cornflower")


def f_nets(c):
    for z in range(c.z1, c.z1 + 4):
        c.S(c.x1 - 2, c.gy + 1, z, c.fence())
        c.S(c.x1 - 2, c.gy + 2, z, c.fence())
    c.S(c.x1 - 3, c.gy + 1, c.z1 + 1, "barrel[facing=up,open=false]")


def f_mage_tower(c):
    tx, tz = c.x2 + 3, c.z1 + 2
    H = c.ytop + 9
    wall = {"Cascadia": "stone_bricks", "Hearthwood": "bricks", "Neoterra": "white_concrete"}[c.style]
    for y in range(c.gy + 1, H + 1):
        for x in range(tx - 2, tx + 3):
            for z in range(tz - 2, tz + 3):
                d = math.hypot(x - tx, z - tz)
                if 1.5 < d <= 2.5:
                    c.S(x, y, z, "purple_stained_glass" if (y % 4 == 0 and (x == tx or z == tz)) else wall)
    r, y = 3, H + 1
    while r >= 0:
        for x in range(tx - r, tx + r + 1):
            for z in range(tz - r, tz + r + 1):
                if math.hypot(x - tx, z - tz) <= r + 0.3:
                    c.S(x, y, z, "purple_terracotta" if c.style != "Neoterra" else "purple_concrete")
        r -= 1
        y += 1
        if r == 0:
            y += 1
    c.S(tx, y, tz, "end_rod[facing=up]")
    # covered link from the tower to the side wall
    for x in range(c.x2 + 1, tx - 1):
        c.S(x, c.gy + 3, tz, f"{c.wood}_slab[type=top,waterlogged=false]" if c.style != "Neoterra" else "smooth_stone_slab[type=top,waterlogged=false]")


def f_steeple(c):
    """Square bell tower on the front gable with a tall spire."""
    xs, zs = range(c.dx - 1, c.dx + 2), range(c.z1, c.z1 + 3)
    base = c.ytop + 1
    ridge = max(c.top(x, z) for x in xs for z in zs)
    top = ridge + 4
    for y in range(base, top + 1):
        for x in xs:
            for z in zs:
                edge = x != c.dx or z != c.z1 + 1
                c.S(x, y, z, (c.M["wall"] if y < top - 1 else c.M["post"]) if edge else AIR, force=True)
    for x, z in ((c.dx, c.z1), (c.dx, c.z1 + 2), (c.dx - 1, c.z1 + 1), (c.dx + 1, c.z1 + 1)):
        c.S(x, top - 1, z, AIR, force=True)
        c.S(x, top, z, AIR, force=True)
    c.S(c.dx, top, c.z1 + 1, "bell[attachment=ceiling,facing=north,powered=false]", force=True)
    for x in xs:
        for z in zs:
            c.S(x, top + 1, z, c.M["ridge"], force=True)
    roof = c.a.M["roof5"] if c.a.top else c.a.M["roof"]
    for k in range(6):
        c.S(c.dx, top + 2 + k, c.z1 + 1, f"{roof}_planks" if roof in ("spruce", "dark_oak", "oak", "birch", "mangrove") else c.M["ridge"], force=True)
    c.S(c.dx, top + 8, c.z1 + 1, "lightning_rod[facing=up,powered=false,waterlogged=false]", force=True)




# ================================================================================================================
# Neoterra vocabulary
def f_glass_canopy(c):
    y = c.gy + 3
    for x in range(c.dx - 3, c.dx + 4):
        for z in range(c.z1 - 3, c.z1):
            c.S(x, y, z, "smooth_quartz_slab[type=top,waterlogged=false]" if z > c.z1 - 3 else "light_blue_stained_glass")


def f_glass_front(c):
    for f in range(c.nf):
        for y in range(c.a.floor_y(f) + 1, c.a.floor_y(f + 1)):
            for x in range(c.x1 + 1, c.x2):
                g = c.get(x, y, c.z1)
                if "door" in g or (x, y, c.z1) in c.a.locked:
                    continue
                c.S(x, y, c.z1, "light_blue_stained_glass_pane")


def f_fins(c):
    for x in range(c.x1 + 1, c.x2, 3):
        if abs(x - c.dx) <= 1:
            continue
        for y in range(c.gy + 1, c.ytop + 1):
            c.S(x, y, c.z1 - 1, "white_concrete")


def f_roof_terrace(c):
    y = c.top(c.cx, c.cz)
    for x in range(c.x1 + 1, c.x2):
        for z in (c.z1 + 1, c.z2 - 1):
            c.S(x, y + 1, z, "light_blue_stained_glass_pane")
    for z in range(c.z1 + 1, c.z2):
        for x in (c.x1 + 1, c.x2 - 1):
            c.S(x, y + 1, z, "light_blue_stained_glass_pane")
    for x in range(c.cx - 2, c.cx + 3, 2):
        c.S(x, y + 1, c.cz, "smooth_quartz_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")


def f_antenna(c):
    x, z = c.x2 - 1, c.z2 - 1
    y = c.top(x, z)
    for k in range(1, 8):
        c.S(x, y + k, z, "iron_bars")
    c.S(x, y + 8, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    c.S(x - 1, y + 5, z, "iron_bars")
    c.S(x + 1 if x + 1 < c.bp.sx else x - 2, y + 5, z, "iron_bars")


def f_screen(c):
    x = c.x1
    for z in range(c.z1 + 2, min(c.z2 - 1, c.z1 + 8)):
        for y in range(c.gy + 2, c.gy + 5):
            edge = z in (c.z1 + 2, min(c.z2 - 2, c.z1 + 7)) or y in (c.gy + 2, c.gy + 4)
            c.S(x - 1, y, z, "cyan_concrete" if edge else "black_concrete")


def f_light_strips(c):
    for f in range(c.nf):
        y = c.a.floor_y(f + 1) - 1 if f < c.nf - 1 else c.ytop - 1
        for x in range(c.x1 + 1, c.x2):
            if "glass" not in c.get(x, y, c.z1) and "door" not in c.get(x, y, c.z1):
                c.S(x, y, c.z1, "sea_lantern")


def f_glass_cube(c):
    xa, xb = c.x2 + 1, c.x2 + 5
    za, zb = c.cz - 2, c.cz + 2
    for x in range(xa, xb + 1):
        for z in range(za, zb + 1):
            e = x in (xa, xb) or z in (za, zb)
            c.S(x, c.gy, z, "smooth_stone")
            for y in range(c.gy + 1, c.gy + 4):
                corner = x in (xa, xb) and z in (za, zb)
                c.S(x, y, z, "white_concrete" if corner else ("light_blue_stained_glass" if e else AIR))
            c.S(x, c.gy + 4, z, "white_concrete" if e else "light_blue_stained_glass")
    for y in (c.gy + 1, c.gy + 2):
        c.S(c.x2, y, c.cz, AIR)
        c.S(xa, y, c.cz, AIR)


def f_solar_roof(c):
    for x in range(c.x1 + 1, c.x2, 1):
        for z in range(c.z1 + 1, c.z2, 2):
            y = c.top(x, z)
            if "pane" in c.get(x, y, z) or "rod" in c.get(x, y, z):
                continue
            c.S(x, y + 1, z, "daylight_detector[inverted=false,power=0]")


def f_conveyor(c):
    z = c.cz
    for x in range(c.x1 - 6, c.x1):
        c.S(x, c.gy + 4, z, "smooth_stone_slab[type=top,waterlogged=false]")
        if (x - c.x1) % 2 == 0:
            for y in range(c.gy + 1, c.gy + 4):
                c.S(x, y, z, "iron_bars")
    c.S(c.x1 - 6, c.gy + 5, z, "iron_block")


def f_cooling_tower(c):
    tx, tz = c.x2 + 5, c.cz
    H = c.ytop + 6
    for y in range(c.gy + 1, H + 1):
        t = (y - c.gy) / (H - c.gy)
        r = 3.4 - 1.6 * math.sin(math.pi * t * 0.85)
        for x in range(tx - 4, tx + 5):
            for z in range(tz - 4, tz + 5):
                d = math.hypot(x - tx, z - tz)
                if r - 1 < d <= r:
                    c.S(x, y, z, "light_gray_concrete" if y % 6 else "white_concrete")


def f_silo_modern(c):
    tx, tz = c.x2 + 4, c.z1 + 2
    H = c.ytop + 7
    for y in range(c.gy + 1, H + 1):
        for x in range(tx - 2, tx + 3):
            for z in range(tz - 2, tz + 3):
                d = math.hypot(x - tx, z - tz)
                if 1.5 < d <= 2.5:
                    c.S(x, y, z, "white_concrete" if (y // 3) % 2 else "light_gray_concrete")
    for x in range(tx - 1, tx + 2):
        for z in range(tz - 1, tz + 2):
            c.S(x, H + 1, z, "smooth_quartz")
    c.S(tx, H + 2, tz, "sea_lantern")
    for y in range(c.gy + 1, H + 1):
        c.S(tx, y, tz - 3, "iron_bars")


# ================================================================================================================
# Hearthwood vocabulary
def f_shutters(c):
    wood = c.wood
    for f in range(c.nf):
        for y in range(c.a.floor_y(f) + 1, c.a.floor_y(f + 1)):
            for x in range(c.x1 + 1, c.x2):
                if "glass" in c.get(x, y, c.z1):
                    for nx in (x - 1, x + 1):
                        if "glass" not in c.get(nx, y, c.z1) and c.get(nx, y, c.z1) != AIR and (nx, y, c.z1 - 1) not in c.a.locked:
                            c.S(nx, y, c.z1 - 1, f"{wood}_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]")


def f_wall_lanterns(c):
    for x in (c.dx - 2, c.dx + 2):
        c.S(x, c.gy + 3, c.z1 - 1, c.fence())
        c.S(x, c.gy + 2, c.z1 - 1, "lantern[hanging=true,waterlogged=false]")


def f_bay_window(c):
    for x0 in (c.dx + 3, c.dx - 5):
        if x0 < c.x1 + 1 or x0 + 2 > c.x2 - 1:
            continue
        for x in range(x0, x0 + 3):
            c.S(x, c.gy + 1, c.z1 - 1, "bricks")
            for y in (c.gy + 2, c.gy + 3):
                c.S(x, y, c.z1 - 1, "glass_pane")
                c.S(x, y, c.z1, "glass_pane")
            c.S(x, c.gy + 4, c.z1 - 1, c.stair(c.wood, "north"))


def f_gable_clock(c):
    y0 = c.ytop + 2
    for dx in (-1, 0, 1):
        for dy in (0, 1, 2):
            if c.get(c.dx + dx, y0 + dy, c.z1) != AIR:
                c.S(c.dx + dx, y0 + dy, c.z1 - 1, "calcite" if (dx, dy) != (0, 1) else "dark_oak_planks")


def f_bench(c):
    for x in (c.dx - 3, c.dx - 2):
        if x > c.x1:
            c.S(x, c.gy + 1, c.z1 - 1, c.stair(c.wood, "south"))


def f_dovecote(c):
    xa, za = c.x1 - 4, c.z1
    for y in range(c.gy + 1, c.gy + 7):
        for x in range(xa, xa + 3):
            for z in range(za, za + 3):
                if x in (xa, xa + 2) or z in (za, za + 2):
                    c.S(x, y, z, "bricks" if y < c.gy + 4 else ("white_terracotta" if (x + z + y) % 2 else AIR))
    for k in range(2):
        for x in range(xa + k, xa + 3 - k):
            for z in range(za + k, za + 3 - k):
                c.S(x, c.gy + 7 + k, z, f"{c.wood}_planks" if k else c.stair(c.wood, "south"))


def f_hoist(c):
    y = c.ytop + 1
    for z in (c.z1 - 1, c.z1 - 2):
        c.S(c.dx, y, z, f"stripped_{c.wood}_log[axis=z]")
    for k in range(1, 4):
        c.S(c.dx, y - k, c.z1 - 2, "chain[axis=y,waterlogged=false]")
    c.S(c.dx, y - 4, c.z1 - 2, f"{c.wood}_planks")


# ================================================================================================================
# Cascadia vocabulary
def f_log_porch(c):
    xa, xb = c.x1, c.x2
    for x in range(xa, xb + 1):
        for z in range(c.z1 - 3, c.z1):
            c.S(x, c.gy, z, "spruce_planks")
        c.S(x, c.gy + 4, c.z1 - 3, "spruce_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")
        for z in (c.z1 - 2, c.z1 - 1):
            c.S(x, c.gy + 4, z, "spruce_planks")
        if (x - xa) % 3 == 0:
            for y in range(c.gy + 1, c.gy + 4):
                c.S(x, y, c.z1 - 3, "stripped_spruce_log[axis=y]")
        elif abs(x - c.dx) > 1:
            c.S(x, c.gy + 1, c.z1 - 3, c.fence("spruce"))


def f_firewood(c):
    x0 = c.x2 + 1
    for z in range(c.z1 + 1, min(c.z2, c.z1 + 6)):
        for y in (c.gy + 1, c.gy + 2):
            c.S(x0, y, z, "spruce_log[axis=x]" if (y + z) % 2 else "birch_log[axis=x]")
        c.S(x0, c.gy + 3, z, "spruce_slab[type=bottom,waterlogged=false]")


def f_rain_barrels(c):
    for x, z in ((c.x1 - 1, c.z1 + 1), (c.x2 + 1, c.z2 - 1)):
        c.S(x, c.gy + 1, z, "water_cauldron[level=2]")
        top = None
        for y in range(c.gy + 3, c.bp.sy):
            if c.get(x, y, z) != AIR:
                top = y
                break
        if top:
            for y in range(c.gy + 2, top):
                c.S(x, y, z, "chain[axis=y,waterlogged=false]")


def f_moss_ridge(c):
    for x in range(c.x1 - 1, c.x2 + 2):
        for z in range(c.z1 - 1, c.z2 + 2):
            y = c.top(x, z)
            if y <= c.ytop:
                continue
            s = c.get(x, y, z)
            if "stairs" in s and (x + z) % 3 == 0:
                c.S(x, y + 1, z, "moss_carpet")
            elif "planks" in s or "slab" in s:
                c.S(x, y, z, "moss_block", force=True)


def f_lantern_posts(c):
    for x in (c.dx - 2, c.dx + 2):
        z = c.z1 - 4 if c.z1 - 4 >= 0 else 0
        for y in range(c.gy + 1, c.gy + 3):
            c.S(x, y, z, "spruce_log[axis=y]")
        c.S(x, c.gy + 3, z, "lantern[hanging=false,waterlogged=false]")


def f_rock_pile(c):
    x0, z0 = c.x1 - 4, c.z2 - 3
    mats = ["mossy_cobblestone", "cobblestone", "andesite", "tuff"]
    for x in range(x0, x0 + 3):
        for z in range(z0, z0 + 3):
            hgt = 1 + (x == x0 + 1 and z == z0 + 1) + ((x + z) % 3 == 0)
            for y in range(c.gy + 1, c.gy + 1 + hgt):
                c.S(x, y, z, mats[(x * 7 + z * 3 + y) % len(mats)])


def f_hay_loft(c):
    y = c.ytop + 2
    if c.get(c.dx, y, c.z1) != AIR:
        c.S(c.dx, y, c.z1, "spruce_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]")
    if c.get(c.dx, y + 2, c.z1) != AIR:
        c.S(c.dx, y + 2, c.z1 - 1, "stripped_spruce_log[axis=z]")
    for x in (c.dx - 4, c.dx - 3, c.dx + 3):
        if c.x1 <= x <= c.x2:
            c.S(x, c.gy + 1, c.z1 - 2, "hay_block[axis=x]")
    c.S(c.dx - 4, c.gy + 2, c.z1 - 2, "hay_block[axis=x]")


def f_mine_portal(c):
    x0, z0 = c.x1 - 6, c.z1
    for x in range(x0, x0 + 5):
        for z in range(z0, z0 + 4):
            for y in range(c.gy + 1, c.gy + 5 - abs(x - (x0 + 2)) // 2):
                c.S(x, y, z, "cobblestone" if (x + y + z) % 3 else "mossy_cobblestone")
    xc = x0 + 2
    for y in (c.gy + 1, c.gy + 2):
        c.S(xc, y, z0, AIR)
        c.S(xc, y, z0 + 1, AIR)
    for x in (xc - 1, xc + 1):
        for y in (c.gy + 1, c.gy + 2):
            c.S(x, y, z0 - 1, "spruce_log[axis=y]")
    for x in range(xc - 1, xc + 2):
        c.S(x, c.gy + 3, z0 - 1, "spruce_log[axis=x]")
    for z in (z0 - 2, z0 - 1, z0, z0 + 1):
        c.S(xc, c.gy + 1, z, "rail[shape=north_south,waterlogged=false]")


# archgen's own extras
PASSTHROUGH = ("porch", "covered_entry", "deck", "dormers", "awning", "silo", "water_wheel", "cupola", "lookout", "sunroom",
               "stone_chimney", "brick_chimney")


def apply(a):
    c = _Ctx(a)
    for lvl, name in a.typ["feats"]:
        if a.L < lvl or name in getattr(a, "skip_feats", ()):
            continue
        if name in PASSTHROUGH:
            a.extra(name)
        else:
            globals()["f_" + name](c)
