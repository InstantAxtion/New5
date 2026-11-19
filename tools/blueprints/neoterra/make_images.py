"""Pack icon, Build Tool category icons and level-progression strips from the rendered previews."""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

pack, prev = Path(sys.argv[1]), Path(sys.argv[2])
ICON = sys.argv[3] if len(sys.argv) > 3 else "neoterra.png"
BG = (236, 240, 244, 255)
# category folder -> building whose level-5 render is used as the tab icon
CATEGORIES = {"fundamentals": "townhall5", "craftsmanship": "deliveryman5", "decorations": "playerhouse5",
              "education": "university5", "military": "barracks5", "agriculture": "farmer5",
              "infrastructure": "miner5", "mystic": "enchanter5", "walls": "watchtower3"}
BUILDINGS = ["townhall", "builder", "cottage", "house", "apartment", "quadplex", "skytower", "bunker",
             "cook", "lumberjack", "sawmill", "stonemason", "mechanic", "deliveryman", "warehouse",
             "school", "library", "university", "guardtower", "barracks", "archery", "combatacademy", "stable",
             "playerhouse", "miner", "farmer", "hospital", "tavern", "fisherman", "smeltery", "blacksmith", "baker",
             "fletcher", "cookery", "alchemist", "dyer", "glassblower", "concretemixer", "crusher", "sifter",
             "stonesmeltery", "florist", "plantation", "composter", "beekeeper", "chickenherder", "cowboy",
             "shepherd", "swineherder", "rabbithutch",
             "enchanter", "graveyard", "mysticalsite", "netherworker", "wallguardtower", "communitycollege", "gatehouse", "watchtower"]


def square(im, bg=BG):
    side = max(im.size)
    out = Image.new("RGBA", (side, side), bg)
    out.paste(im, ((side - im.width) // 2, (side - im.height) // 2), im)
    return out


square(Image.open(prev / "townhall5_front.png").convert("RGBA")).resize((128, 128), Image.LANCZOS) \
    .save(pack / ICON)

for cat, b in CATEGORIES.items():
    src = prev / f"{b}_front.png"
    if not src.exists():
        continue
    icon = square(Image.open(src).convert("RGBA"), (0, 0, 0, 0)).resize((20, 20), Image.LANCZOS)
    (pack / cat).mkdir(parents=True, exist_ok=True)
    icon.save(pack / cat / "icon.png")
    gray = ImageOps.grayscale(icon.convert("RGB")).convert("RGBA")
    gray.putalpha(icon.getchannel("A"))
    gray.save(pack / cat / "icon_disabled.png")

for b in BUILDINGS:
    files = [prev / f"{b}{lvl}_front.png" for lvl in range(1, 6) if (prev / f"{b}{lvl}_front.png").exists()]
    if not files:
        continue
    ims = [Image.open(f).convert("RGBA") for f in files]
    scale = 420 / max(i.height for i in ims)
    ims = [i.resize((int(i.width * scale), int(i.height * scale)), Image.LANCZOS) for i in ims]
    strip = Image.new("RGBA", (sum(i.width for i in ims) + 20 * 6, 470), BG)
    d = ImageDraw.Draw(strip)
    x = 20
    for n, im in enumerate(ims, 1):
        strip.paste(im, (x, 470 - 30 - im.height), im)
        d.text((x + im.width // 2 - 20, 445), f"Level {n}", fill=(40, 40, 40, 255))
        x += im.width + 20
    strip.convert("RGB").save(prev / f"{b}_levels.png")
