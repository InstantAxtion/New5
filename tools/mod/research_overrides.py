"""
Make every MineColonies research free and 10x faster: writes data overrides into the mod's resources.

  * research files (data/minecolonies/researches/<branch>/<id>.json): item "costs" removed – building
    requirements (e.g. "University level 2") stay, they are what unlocks a research, not what it costs.
  * branch files (data/minecolonies/researches/<branch>.json): "base-time" divided by SPEED.
    MineColonies' research time = 72 * base-time * 2^(level-1) progress units, so 1/10 base time = 10x speed.

The overrides load after MineColonies' own data (the mod depends on MineColonies, ordering AFTER).
usage: python research_overrides.py [minecolonies jar]   (default: the jar in the Gradle cache)
"""
import glob
import json
import sys
import zipfile
from pathlib import Path

SPEED = 10
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "mod/src/main/resources/data/minecolonies/researches"


def main():
    jar = sys.argv[1] if len(sys.argv) > 1 else sorted(glob.glob(
        "/root/.gradle/caches/modules-2/files-2.1/com.ldtteam/minecolonies/*/*/minecolonies-*.jar"))[-1]
    n_free = n_branch = 0
    with zipfile.ZipFile(jar) as z:
        for name in z.namelist():
            if not (name.startswith("data/minecolonies/researches/") and name.endswith(".json")):
                continue
            rel = name[len("data/minecolonies/researches/"):]
            if rel.startswith("effects/"):
                continue
            data = json.loads(z.read(name))
            if "base-time" in data:
                data["base-time"] = round(float(data["base-time"]) / SPEED, 4)
                n_branch += 1
            elif "costs" in data:
                data["costs"] = []
                n_free += 1
            else:
                continue
            dst = OUT / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(json.dumps(data, indent=2) + "\n")
    print(f"research overrides: {n_free} researches made free, {n_branch} branches {SPEED}x faster -> {OUT}")


if __name__ == "__main__":
    main()
