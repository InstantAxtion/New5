"""Pack icon, Build Tool category icons and level-progression strips from the rendered previews."""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

pack, prev = Path(sys.argv[1]), Path(sys.argv[2])
BG = (236, 240, 244, 255)
# category folder -> building whose level-5 render is used as the tab icon
CATEGORIES = {"fundamentals": "townhall", "craftsmanship": "deliveryman"}
BUILDINGS = ["townhall", "builder", "deliveryman", "warehouse"]


def square(im, bg=BG):
    side = max(im.size)
    out = Image.new("RGBA", (side, side), bg)
    out.paste(im, ((side - im.width) // 2, (side - im.height) // 2), im)
    return out


square(Image.open(prev / "townhall5_front.png").convert("RGBA")).resize((128, 128), Image.LANCZOS) \
    .save(pack / "neoterra.png")

for cat, b in CATEGORIES.items():
    src = prev / f"{b}5_front.png"
    if not src.exists():
        continue
    icon = square(Image.open(src).convert("RGBA"), (0, 0, 0, 0)).resize((20, 20), Image.LANCZOS)
    (pack / cat).mkdir(parents=True, exist_ok=True)
    icon.save(pack / cat / "icon.png")
    gray = ImageOps.grayscale(icon.convert("RGB")).convert("RGBA")
    gray.putalpha(icon.getchannel("A"))
    gray.save(pack / cat / "icon_disabled.png")

for b in BUILDINGS:
    files = [prev / f"{b}{lvl}_front.png" for lvl in range(1, 6)]
    if not all(f.exists() for f in files):
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
