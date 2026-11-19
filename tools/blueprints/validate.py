"""
Validate every block state in .blueprint files.

usage: python validate.py <minecraft-data blocks.json for 1.21.1> <file.blueprint>...
(blocks.json: https://raw.githubusercontent.com/PrismarineJS/minecraft-data/master/data/pc/1.21.1/blocks.json)
Vanilla blocks are checked by name + property values. Modded blocks are checked against the
known lists below (taken from Domum Ornamentum 1.21.1 / MineColonies / Structurize).
"""
import json
import sys
from pathlib import Path

import nbtlib

MODDED = {
    "minecolonies:blockhuttownhall": {"facing"},
    "minecolonies:blockhutdeliveryman": {"facing"},
    "minecolonies:blockhutwarehouse": {"facing"},
    "minecolonies:blockhutbuilder": {"facing"},
    "neoterra:blockhutsupplydepot": {"facing"}, "neoterra:blockhutcathedral": {"facing"}, "neoterra:blockhutgrandbridge": {"facing"},
    "neoterra:blockhutcolossus": {"facing"}, "neoterra:blockhutroyalgranary": {"facing"}, "neoterra:blockhutwonderwing": {"facing"},
    "neoterra:blockhuttradepost": {"facing"},
    "minecolonies:blockhutcitizen": {"facing"},
    "minecolonies:blockhutcook": {"facing"},
    "minecolonies:blockhutlumberjack": {"facing"},
    "minecolonies:blockhutsawmill": {"facing"},
    "minecolonies:blockhutstonemason": {"facing"},
    "minecolonies:blockhutmechanic": {"facing"},
    "minecolonies:blockhutuniversity": {"facing"},
    "minecolonies:blockhutschool": {"facing"},
    "minecolonies:blockhutlibrary": {"facing"},
    "minecolonies:blockhutarchery": {"facing"},
    "minecolonies:blockhutbarracks": {"facing"},
    "minecolonies:blockhutbarrackstower": {"facing"},
    "minecolonies:blockhutcombatacademy": {"facing"},
    "minecolonies:blockhutguardtower": {"facing"},
    "minecolonies:blockhutstable": {"facing"},
    "minecolonies:blockhuthospital": {"facing"},
    "minecolonies:blockhutfarmer": {"facing"},
    "minecolonies:blockhutfield": {"facing", "half"},
    "minecolonies:blockhutminer": {"facing"},
    "minecolonies:blockhuttavern": {"facing"},
    "minecolonies:blockhutfisherman": {"facing"},
    "minecolonies:blockhutsmeltery": {"facing"},
    "minecolonies:blockhutblacksmith": {"facing"},
    "minecolonies:blockhutbaker": {"facing"},
    "minecolonies:blockhutenchanter": {"facing"},
    "minecolonies:blockhutgraveyard": {"facing"},
    "minecolonies:blockhutmysticalsite": {"facing"},
    "minecolonies:blockhutnetherworker": {"facing"},
    "minecolonies:blockhutgatehouse": {"facing"},
    "minecolonies:simplequarry": {"facing"},
    "minecolonies:mediumquarry": {"facing"},
    "minecolonies:blockminecoloniesnamedgrave": {"facing"},
    "minecolonies:gate_iron": {"facing", "half", "hinge", "open", "powered"},
    "minecolonies:blockhutfletcher": {"facing"},
    "minecolonies:blockhutkitchen": {"facing"},
    "minecolonies:blockhutalchemist": {"facing"},
    "minecolonies:blockhutdyer": {"facing"},
    "minecolonies:blockhutglassblower": {"facing"},
    "minecolonies:blockhutconcretemixer": {"facing"},
    "minecolonies:blockhutcrusher": {"facing"},
    "minecolonies:blockhutsifter": {"facing"},
    "minecolonies:blockhutstonesmeltery": {"facing"},
    "minecolonies:blockhutflorist": {"facing"},
    "minecolonies:blockhutplantation": {"facing"},
    "minecolonies:blockhutcomposter": {"facing"},
    "minecolonies:blockhutbeekeeper": {"facing"},
    "minecolonies:blockhutchickenherder": {"facing"},
    "minecolonies:blockhutcowboy": {"facing"},
    "minecolonies:blockhutshepherd": {"facing"},
    "minecolonies:blockhutswineherder": {"facing"},
    "minecolonies:blockhutrabbithutch": {"facing"},
    "minecolonies:blockhutplantationfield": {"facing", "mirror"},
    "minecolonies:barrel_block": {"facing", "variant"},
    "minecolonies:composted_dirt": set(),
    "structurize:blocktagsubstitution": set(),
    "structurize:blockfluidsubstitution": set(),
    "minecolonies:decorationcontroller": {"facing", "mirror", "waterlogged"},
    "domum_ornamentum:architectscutter": {"facing"},
    "minecolonies:blockminecoloniesrack": {"facing", "variant"},
    "structurize:blocksolidsubstitution": set(),
    "structurize:blocksubstitution": set(),
    "domum_ornamentum:vanilla_slab_compat": {"type", "waterlogged"},
    "domum_ornamentum:vanilla_stairs_compat": {"facing", "half", "shape", "waterlogged"},
    "domum_ornamentum:blockpillar": {"column"},
    "domum_ornamentum:blockpaperwall": {"north", "south", "east", "west", "waterlogged"},
    "domum_ornamentum:fancy_light": set(),
    "domum_ornamentum:shingle": {"facing", "half", "shape", "waterlogged"},
    "domum_ornamentum:shingle_slab": {"facing", "shape", "waterlogged"},
    "domum_ornamentum:plain": {"facing"}, "domum_ornamentum:double_crossed": {"facing"},
    "domum_ornamentum:one_crossed_lr": {"facing"}, "domum_ornamentum:one_crossed_rl": {"facing"},
    "domum_ornamentum:framed": {"facing"}, "domum_ornamentum:horizontal_plain": {"facing"},
    "domum_ornamentum:side_framed": {"facing"}, "domum_ornamentum:squarepillar": {"column"},
    "domum_ornamentum:panel": {"facing", "half", "open", "type", "waterlogged"},
    "domum_ornamentum:vanilla_trapdoors_compat": {"facing", "half", "open", "powered", "type", "waterlogged"},
    "domum_ornamentum:center_light": set(),
}


def main():
    data = {b["name"]: b for b in json.load(open(sys.argv[1]))}
    bad = 0
    for f in sys.argv[2:]:
        root = nbtlib.load(f)
        for c in root["palette"]:
            n = str(c["Name"])
            props = {str(k): str(v) for k, v in c.get("Properties", {}).items()}
            ns, short = n.split(":")
            if ns != "minecraft":
                if n not in MODDED or not set(props) <= MODDED[n]:
                    print(f"{Path(f).name}: unknown modded state {n} {props}")
                    bad += 1
                continue
            b = data.get(short)
            if b is None:
                print(f"{Path(f).name}: unknown block {n}")
                bad += 1
                continue
            states = {s["name"]: s for s in b.get("states", [])}
            for k, v in props.items():
                s = states.get(k)
                if s is None:
                    print(f"{Path(f).name}: {n} has no property {k}")
                    bad += 1
                    continue
                vals = s.get("values") or (["true", "false"] if s["type"] == "bool"
                                           else [str(i) for i in range(s.get("num_values", 0))])
                if s["type"] == "int":
                    vals = [str(i) for i in range(16)]
                if v not in vals:
                    print(f"{Path(f).name}: {n} {k}={v} not in {vals}")
                    bad += 1
        for te in root["tile_entities"]:
            td = te.get("textureData")
            if td:
                for comp, mat in td.items():
                    if str(mat).startswith("minecraft:") and str(mat).split(":")[1] not in data:
                        print(f"{Path(f).name}: DO material {mat} is not a block")
                        bad += 1
    print("OK" if not bad else f"{bad} problems")
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
