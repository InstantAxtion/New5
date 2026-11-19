"""
Package the Neoterra style pack for players.

  dist/Neoterra-<ver>.jar   no-code NeoForge mod (lowcodefml) – drop into the instance's `mods` folder.
                            Structurize loads packs from  blueprints/<modid>/<Pack>/pack.json  inside mod jars.
  dist/Neoterra-<ver>.zip   download bundle containing the jar.
"""
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACK = ROOT / "stylepacks" / "Neoterra"
DIST = ROOT / "dist"
VERSION = sys.argv[1] if len(sys.argv) > 1 else "1.4.1"
MODID = "neoterra"

MODS_TOML = f'''modLoader = "lowcodefml"
loaderVersion = "[1,)"
license = "GPL-3.0"
issueTrackerURL = ""

[[mods]]
modId = "{MODID}"
version = "{VERSION}"
displayName = "Neoterra Style Pack"
authors = "New5"
logoFile = "neoterra.png"
description = """
Neoterra – a semi-futuristic MineColonies style pack: white concrete, light-blue glass, cyan accents,
glowing light strips and trees. 372 blueprints: every hut levels 1-5 (1-3 cheaper, 4-5 premium),
residences, player house and bunker, walls, roads, rails, canals, bridges, subway and parks.
"""

[[dependencies.{MODID}]]
modId = "minecolonies"
type = "required"
versionRange = "*"
ordering = "AFTER"
side = "BOTH"

[[dependencies.{MODID}]]
modId = "structurize"
type = "required"
versionRange = "*"
ordering = "AFTER"
side = "BOTH"

[[dependencies.{MODID}]]
modId = "domum_ornamentum"
type = "required"
versionRange = "*"
ordering = "AFTER"
side = "BOTH"
'''

PACK_MCMETA = '{"pack": {"description": "Neoterra style pack resources", "pack_format": 34}}\n'


def pack_files():
    for f in sorted(PACK.rglob("*")):
        if f.is_file():
            yield f, f.relative_to(PACK).as_posix()


def main():
    DIST.mkdir(exist_ok=True)
    jar = DIST / f"Neoterra-{VERSION}.jar"
    with zipfile.ZipFile(jar, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\nImplementation-Title: Neoterra\n"
                   f"Implementation-Version: {VERSION}\n")
        z.writestr("META-INF/neoforge.mods.toml", MODS_TOML)
        z.writestr("pack.mcmeta", PACK_MCMETA)
        z.write(PACK / "neoterra.png", "neoterra.png")
        for f, rel in pack_files():
            z.write(f, f"blueprints/{MODID}/Neoterra/{rel}")
    bundle = DIST / f"Neoterra-{VERSION}.zip"                          # download: the zip holds the jar
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(jar, jar.name)
    for p in (jar, bundle):
        print(f"{p.relative_to(ROOT)}  {p.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
