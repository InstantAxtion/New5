"""
Package the Neoterra style pack for players.

  dist/Neoterra-<ver>.jar   NeoForge mod – drop into the instance's `mods` folder. Holds the compiled Trade Post
                            mod (built with Gradle from mod/) and the four style packs; Structurize loads packs
                            from  blueprints/<modid>/<Pack>/pack.json  inside mod jars.
  dist/Neoterra-<ver>.zip   download bundle containing the jar.
"""
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACK = ROOT / "stylepacks" / "Neoterra"
DIST = ROOT / "dist"
VERSION = sys.argv[1] if len(sys.argv) > 1 else "1.11.0"
MOD = ROOT / "mod"
MODID = "neoterra"

MODS_TOML = f'''modLoader = "javafml"
loaderVersion = "[1,)"
license = "GPL-3.0"
issueTrackerURL = ""

[[mods]]
modId = "{MODID}"
version = "{VERSION}"
displayName = "Neoterra Style Packs + Trade Post"
authors = "New5"
logoFile = "neoterra_logo.png"
description = """
Three hand-designed MineColonies style packs, vanilla blocks only, every building growing from a modest level-1
hut into a whole complex by level 5:
  Hearthwood - English village: brick, plaster and timber framing, slate and tile roofs, chimneys and gardens.
  Cascadia   - Pacific Northwest timber town: log and board walls, river rock, dark shake roofs, porches.
  Neoterra   - modern city: white concrete, glass, roof gardens and coloured accents.
Plus Farmworks (automatic mob and food farms) and the Trade Post: link two of your colonies and a Trade Courier
carries what one colony needs from the other.
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

[[mixins]]
config = "neoterra.mixins.json"
'''

PACK_MCMETA = '{"pack": {"description": "Neoterra style pack resources", "pack_format": 34}}\n'


PACKS = [ROOT / "stylepacks" / n for n in ("Neoterra", "Hearthwood", "Cascadia", "Farmworks")]


def pack_files(pack):
    for f in sorted(pack.rglob("*")):
        if f.is_file():
            yield f, f.relative_to(pack).as_posix()


def gradle_jar():
    """Compile the Trade Post mod; its jar already contains the four packs (see mod/build.gradle)."""
    subprocess.run(["gradle", "jar", "--no-daemon", "-q", f"-Pmod_version={VERSION}"], cwd=MOD, check=True)
    return MOD / "build" / "libs" / f"neoterra-{VERSION}.jar"


def main():
    DIST.mkdir(exist_ok=True)
    built = gradle_jar()
    jar = DIST / f"Neoterra-{VERSION}.jar"
    names = set()
    with zipfile.ZipFile(jar, "w", zipfile.ZIP_DEFLATED) as z, zipfile.ZipFile(built) as src:
        z.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\nImplementation-Title: Neoterra\n"
                   f"Implementation-Version: {VERSION}\n")
        z.writestr("META-INF/neoforge.mods.toml", MODS_TOML)
        z.writestr("pack.mcmeta", PACK_MCMETA)
        for info in src.infolist():
            if info.filename in ("META-INF/MANIFEST.MF", "META-INF/neoforge.mods.toml", "pack.mcmeta") or info.is_dir():
                continue
            z.writestr(info.filename, src.read(info.filename))
            names.add(info.filename)
    missing = [p.name for p in PACKS if f"blueprints/{MODID}/{p.name}/pack.json" not in names]
    if missing or "com/neoterra/trade/NeoterraTrade.class" not in names:
        raise SystemExit(f"jar incomplete: missing packs {missing} or classes")
    bundle = DIST / f"Neoterra-{VERSION}.zip"                          # download: the zip holds the jar
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(jar, jar.name)
    for p in (jar, bundle):
        print(f"{p.relative_to(ROOT)}  {p.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
