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
VERSION = sys.argv[1] if len(sys.argv) > 1 else "1.8.0"
MODID = "neoterra"

MODS_TOML = f'''modLoader = "lowcodefml"
loaderVersion = "[1,)"
license = "GPL-3.0"
issueTrackerURL = ""

[[mods]]
modId = "{MODID}"
version = "{VERSION}"
displayName = "Neoterra, Hearthwood & Cascadia Style Packs"
authors = "New5"
logoFile = "neoterra.png"
description = """
Three MineColonies style packs: Neoterra (semi-futuristic white, glass and light, every building with its own
theme and landmarks) and Hearthwood (cozy modern: warm plaster, wood cladding, brick and lantern light, easy-to-
medium blocks until level 5) and Cascadia (Oregon / Pacific Northwest: cedar and fir timber, river rock, moss
roofs, basalt). Every hut levels 1-5, residences, player house and bunker, walls, roads and parks.
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


PACKS = [ROOT / "stylepacks" / n for n in ("Neoterra", "Hearthwood", "Cascadia")]


def pack_files(pack):
    for f in sorted(pack.rglob("*")):
        if f.is_file():
            yield f, f.relative_to(pack).as_posix()


def main():
    DIST.mkdir(exist_ok=True)
    jar = DIST / f"Neoterra-{VERSION}.jar"
    with zipfile.ZipFile(jar, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\nImplementation-Title: Neoterra\n"
                   f"Implementation-Version: {VERSION}\n")
        z.writestr("META-INF/neoforge.mods.toml", MODS_TOML)
        z.writestr("pack.mcmeta", PACK_MCMETA)
        z.write(PACK / "neoterra.png", "neoterra.png")
        for pack in PACKS:
            if not pack.exists():
                continue
            for f, rel in pack_files(pack):
                z.write(f, f"blueprints/{MODID}/{pack.name}/{rel}")
    bundle = DIST / f"Neoterra-{VERSION}.zip"                          # download: the zip holds the jar
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(jar, jar.name)
    for p in (jar, bundle):
        print(f"{p.relative_to(ROOT)}  {p.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
