"""Pack icon, category icons and a level-progression strip from the rendered previews."""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

pack, prev = Path(sys.argv[1]), Path(sys.argv[2])
BG = (236, 240, 244, 255)


def square(im, bg=BG):
    side = max(im.size)
    out = Image.new("RGBA", (side, side), bg)
    out.paste(im, ((side - im.width) // 2, (side - im.height) // 2), im)
    return out


top = Image.open(prev / "townhall5_front.png").convert("RGBA")
square(top).resize((128, 128), Image.LANCZOS).save(pack / "neoterra.png")

icon = square(top, (0, 0, 0, 0)).resize((20, 20), Image.LANCZOS)
icon.save(pack / "fundamentals" / "icon.png")
gray = ImageOps.grayscale(icon.convert("RGB")).convert("RGBA")
gray.putalpha(icon.getchannel("A"))
gray.save(pack / "fundamentals" / "icon_disabled.png")

ims = [Image.open(prev / f"townhall{l}_front.png").convert("RGBA") for l in range(1, 6)]
h = max(i.height for i in ims)
scale = 420 / h
ims = [i.resize((int(i.width * scale), int(i.height * scale)), Image.LANCZOS) for i in ims]
W = sum(i.width for i in ims) + 20 * 6
strip = Image.new("RGBA", (W, 470), BG)
d = ImageDraw.Draw(strip)
x = 20
for n, im in enumerate(ims, 1):
    strip.paste(im, (x, 470 - 30 - im.height), im)
    d.text((x + im.width // 2 - 20, 445), f"Level {n}", fill=(40, 40, 40, 255))
    x += im.width + 20
strip.convert("RGB").save(prev / "townhall_levels.png")
