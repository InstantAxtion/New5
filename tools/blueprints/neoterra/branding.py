"""
Logos and build-menu icons, drawn per pack in its own emblem style.

  Neoterra    sleek tech mark: navy rounded tile, cyan rim, glowing skyline
  Hearthwood  heraldic shield: deep red field, gold rim, cream charges (cottage, hearth flame, oak)
  Cascadia    rustic badge: forest-green disc in a timber ring, snow peaks, firs, river
  Farmworks   farm sign: wheat-gold tile, brown rim, barn and gear

Writes
  stylepacks/<Pack>/<pack>.png                  pack logo (128 x 128, build tool pack list)
  stylepacks/<Pack>/**/icon.png, icon_disabled.png  category / sub-category icons (20 x 20)
  mod/src/main/resources/neoterra_logo.png      logo for the game's Mods list
  docs/branding/*.png                           logo, banner, square icon and an overview sheet

usage: python branding.py [<repo root>]
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
FONT_SANS = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
FONT_SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"

STYLE = {
    "Neoterra": dict(shape="tile", fill=(14, 26, 44), fill2=(24, 52, 78), rim=(46, 226, 236), glyph=(214, 250, 255),
                     accent=(46, 226, 236)),
    "Hearthwood": dict(shape="shield", fill=(128, 34, 30), fill2=(168, 52, 42), rim=(226, 184, 92), glyph=(248, 234, 204),
                       accent=(226, 184, 92)),
    "Cascadia": dict(shape="disc", fill=(34, 78, 52), fill2=(52, 104, 70), rim=(132, 88, 48), glyph=(242, 228, 192),
                     accent=(196, 76, 52)),
    "Farmworks": dict(shape="tile", fill=(214, 168, 58), fill2=(232, 196, 92), rim=(104, 64, 30), glyph=(84, 48, 22),
                      accent=(176, 46, 38)),
}


# ------------------------------------------------------------------------------------------------ drawing helpers
class Pen:
    """Draws in a 100 x 100 design space onto a supersampled canvas."""

    def __init__(self, img, box, color, bg):
        self.d = ImageDraw.Draw(img)
        self.x0, self.y0, self.s = box[0], box[1], (box[2] - box[0]) / 100.0
        self.c, self.bg = color, bg

    def P(self, pts):
        return [(self.x0 + x * self.s, self.y0 + y * self.s) for x, y in pts]

    def poly(self, pts, c=None):
        self.d.polygon(self.P(pts), fill=c or self.c)

    def rect(self, x1, y1, x2, y2, c=None, r=0):
        a, b = self.P([(x1, y1), (x2, y2)])
        if r:
            self.d.rounded_rectangle([a, b], radius=r * self.s, fill=c or self.c)
        else:
            self.d.rectangle([a, b], fill=c or self.c)

    def ell(self, x1, y1, x2, y2, c=None):
        a, b = self.P([(x1, y1), (x2, y2)])
        self.d.ellipse([a, b], fill=c or self.c)

    def line(self, pts, w, c=None):
        self.d.line(self.P(pts), fill=c or self.c, width=max(1, int(w * self.s)), joint="curve")

    def arc(self, x1, y1, x2, y2, a1, a2, w, c=None):
        a, b = self.P([(x1, y1), (x2, y2)])
        self.d.arc([a, b], a1, a2, fill=c or self.c, width=max(1, int(w * self.s)))


# ------------------------------------------------------------------------------------------------ glyphs (100x100)
def g_house(p, flag=False, chimney=False):
    p.poly([(12, 50), (50, 16), (88, 50)])
    p.rect(22, 48, 78, 86)
    p.rect(43, 62, 57, 86, p.bg)
    p.rect(28, 56, 38, 66, p.bg)
    p.rect(62, 56, 72, 66, p.bg)
    if chimney:
        p.rect(66, 18, 76, 40)
    if flag:
        p.line([(50, 18), (50, 4)], 3)
        p.poly([(50, 4), (66, 8), (50, 12)])


def g_wheat(p):
    p.line([(50, 92), (50, 18)], 5)
    for i, y in enumerate(range(24, 72, 11)):
        p.ell(30, y, 48, y + 10)
        p.ell(52, y, 70, y + 10)
    p.ell(43, 10, 57, 26)


def g_sprout(p):
    for y in (74, 86):
        p.rect(10, y, 90, y + 6, r=2)
    p.line([(50, 74), (50, 40)], 5)
    p.poly([(50, 46), (24, 30), (20, 48), (36, 54)])
    p.poly([(50, 40), (78, 20), (82, 40), (64, 48)])


def g_flower(p):
    p.line([(50, 92), (50, 56)], 5)
    p.poly([(50, 76), (30, 64), (34, 78)])
    for k in range(6):
        a = k * math.pi / 3
        cx, cy = 50 + 18 * math.cos(a), 38 + 18 * math.sin(a)
        p.ell(cx - 12, cy - 12, cx + 12, cy + 12)
    p.ell(40, 28, 60, 48, p.bg)
    p.ell(44, 32, 56, 44)


def g_horseshoe(p):
    p.arc(18, 14, 82, 78, 140, 400, 15)
    for x, y in ((24, 66), (76, 66)):
        p.rect(x - 9, y, x + 9, y + 20, r=3)
    for a in (160, 200, 340, 380):
        r = math.radians(a)
        cx, cy = 50 + 32 * math.cos(r), 46 + 32 * math.sin(r)
        p.ell(cx - 3, cy - 3, cx + 3, cy + 3, p.bg)


def g_hammer(p):
    p.line([(26, 88), (62, 40)], 9)
    p.poly([(44, 22), (72, 12), (90, 36), (62, 46)])


def g_saw(p):
    p.poly([(12, 40), (78, 30), (82, 56), (12, 58)])
    for x in range(14, 80, 9):
        p.poly([(x, 58), (x + 4.5, 68), (x + 9, 58)])
    p.rect(78, 24, 92, 64, r=4)
    p.rect(82, 34, 88, 54, p.bg, r=2)


def g_gem(p):
    p.poly([(26, 30), (74, 30), (90, 46), (50, 90), (10, 46)])
    p.line([(10, 46), (90, 46)], 3, p.bg)
    p.line([(36, 30), (30, 46), (50, 90), (70, 46), (64, 30)], 3, p.bg)
    p.line([(30, 46), (50, 30), (70, 46)], 3, p.bg)


def g_bricks(p):
    for r, y in enumerate((18, 42, 66)):
        off = 0 if r % 2 == 0 else 14
        x = 8 - off
        while x < 92:
            p.rect(max(8, x), y, min(92, x + 26), y + 18, r=2)
            x += 30


def g_anvil(p):
    p.poly([(10, 26), (78, 26), (92, 30), (86, 40), (66, 44), (60, 58), (36, 58), (32, 44), (16, 40)])
    p.poly([(34, 58), (62, 58), (70, 76), (26, 76)])
    p.rect(18, 76, 78, 88, r=3)


def g_crate(p):
    p.rect(14, 14, 86, 86, r=3)
    p.rect(22, 22, 78, 78, p.bg)
    p.line([(22, 22), (78, 78)], 8)
    p.line([(78, 22), (22, 78)], 8)
    p.rect(14, 46, 86, 54)


def g_lantern(p):
    p.arc(36, 4, 64, 30, 180, 360, 5)
    p.rect(30, 18, 70, 26, r=2)
    p.rect(26, 26, 74, 84, r=5)
    p.rect(34, 34, 66, 76, p.bg, r=3)
    p.ell(42, 44, 58, 70)
    p.rect(30, 84, 70, 92, r=2)


def g_tree(p):
    p.rect(44, 62, 56, 92)
    p.ell(18, 10, 82, 72)
    p.ell(10, 34, 46, 66)
    p.ell(54, 34, 90, 66)


def g_chest(p):
    p.rect(10, 30, 90, 86, r=5)
    p.rect(16, 50, 84, 80, p.bg, r=2)
    p.rect(10, 44, 90, 52)
    p.rect(42, 40, 58, 60, r=3)
    p.rect(47, 46, 53, 54, p.bg)


def g_book(p):
    p.poly([(50, 28), (14, 18), (8, 80), (50, 90)])
    p.poly([(50, 28), (86, 18), (92, 80), (50, 90)])
    for y in (36, 48, 60):
        p.line([(18, y - 6), (44, y)], 3, p.bg)
        p.line([(56, y), (82, y - 6)], 3, p.bg)
    p.line([(50, 28), (50, 90)], 3, p.bg)


def g_swords(p):
    for flip in (1, -1):
        def X(x):
            return x if flip == 1 else 100 - x
        p.line([(X(18), 18), (X(76), 76)], 8)
        p.poly([(X(14), 10), (X(26), 14), (X(18), 22)])
        p.line([(X(60), 82), (X(84), 58)], 6)
        p.line([(X(76), 76), (X(88), 88)], 7)


def g_star(p):
    pts = []
    for k in range(10):
        r = 44 if k % 2 == 0 else 18
        a = -math.pi / 2 + k * math.pi / 5
        pts.append((50 + r * math.cos(a), 52 + r * math.sin(a)))
    p.poly(pts)
    for cx, cy in ((84, 16), (16, 22)):
        p.poly([(cx, cy - 8), (cx + 3, cy), (cx, cy + 8), (cx - 3, cy)])


def g_wall(p):
    p.rect(8, 40, 92, 90)
    for x in range(8, 92, 18):
        p.rect(x, 22, x + 11, 42)
    p.arc(36, 62, 64, 100, 180, 360, 30, p.bg)
    for y in (54, 72):
        p.line([(8, y), (30, y)], 2, p.bg)
        p.line([(70, y), (92, y)], 2, p.bg)


def g_bridge(p):
    p.rect(4, 30, 96, 40)
    p.arc(14, 38, 86, 118, 180, 360, 12)
    for x in (22, 36, 50, 64, 78):
        p.line([(x, 40), (x, 48 + abs(50 - x) * 0.5)], 3)
    p.rect(4, 40, 14, 92)
    p.rect(86, 40, 96, 92)


def g_road(p):
    p.poly([(36, 6), (64, 6), (94, 94), (6, 94)])
    for y1, y2 in ((12, 26), (36, 52), (62, 84)):
        w = 2 + y2 * 0.04
        p.poly([(50 - w, y1), (50 + w, y1), (50 + w * 1.2, y2), (50 - w * 1.2, y2)], p.bg)


def g_rails(p):
    for y in range(14, 92, 14):
        p.rect(16, y, 84, y + 6, r=2)
    p.rect(28, 6, 36, 94)
    p.rect(64, 6, 72, 94)


def g_canal(p):
    for y in (28, 50, 72):
        pts = [(x, y + 7 * math.sin(x / 100 * 2 * math.pi * 1.5)) for x in range(6, 96, 3)]
        p.line(pts, 8)


def g_boardwalk(p):
    for x in range(10, 90, 16):
        p.rect(x, 20, x + 12, 76, r=2)
    p.rect(14, 76, 22, 94)
    p.rect(78, 76, 86, 94)


def g_ladder(p):
    p.rect(24, 4, 32, 96)
    p.rect(68, 4, 76, 96)
    for y in range(14, 96, 16):
        p.rect(32, y, 68, y + 6)
    p.poly([(80, 30), (96, 50), (80, 70)])


def g_pickaxe(p):
    p.line([(22, 90), (66, 30)], 8)
    p.arc(10, 6, 96, 70, 200, 330, 10)


def g_train(p):
    p.rect(16, 8, 84, 80, r=14)
    p.rect(24, 18, 76, 46, p.bg, r=6)
    p.ell(24, 56, 38, 70, p.bg)
    p.ell(62, 56, 76, 70, p.bg)
    p.poly([(24, 80), (34, 80), (22, 96), (12, 96)])
    p.poly([(66, 80), (76, 80), (88, 96), (78, 96)])


def g_crown(p):
    p.poly([(10, 34), (30, 56), (50, 22), (70, 56), (90, 34), (82, 78), (18, 78)])
    p.rect(18, 80, 82, 90, r=2)
    for cx, cy in ((10, 30), (50, 18), (90, 30)):
        p.ell(cx - 6, cy - 6, cx + 6, cy + 6)
    p.ell(44, 58, 56, 70, p.bg)


def g_scales(p):
    p.rect(46, 14, 54, 86)
    p.rect(28, 84, 72, 92, r=3)
    p.line([(12, 24), (88, 24)], 6)
    for cx in (20, 80):
        p.line([(cx, 24), (cx - 12, 56)], 2)
        p.line([(cx, 24), (cx + 12, 56)], 2)
        p.poly([(cx - 16, 56), (cx + 16, 56), (cx + 10, 66), (cx - 10, 66)])


def g_egg(p):
    p.ell(26, 14, 74, 90)
    p.ell(36, 28, 48, 44, p.bg)


def g_skull(p):
    p.ell(16, 10, 84, 70)
    p.rect(28, 56, 72, 86, r=6)
    p.ell(28, 34, 46, 52, p.bg)
    p.ell(54, 34, 72, 52, p.bg)
    p.poly([(50, 54), (45, 64), (55, 64)], p.bg)
    for x in (36, 46, 56):
        p.rect(x, 76, x + 6, 86, p.bg)


def g_fields(p):
    for x in (14, 42, 70):
        p.line([(x + 8, 90), (x + 8, 30)], 4)
        p.ell(x, 20, x + 16, 40)
    p.rect(6, 88, 94, 94)


GLYPHS = {
    "fundamentals": lambda p: g_house(p, flag=True), "housing": lambda p: g_house(p, chimney=True),
    "agriculture": g_wheat, "fields": g_sprout, "horticulture": g_flower, "husbandry": g_horseshoe,
    "craftsmanship": g_hammer, "carpentry": g_saw, "luxury": g_gem, "masonry": g_bricks, "metallurgy": g_anvil,
    "storage": g_crate, "decorations": g_lantern, "parks": g_tree, "supplies": g_chest, "education": g_book,
    "military": g_swords, "mystic": g_star, "walls": g_wall, "infrastructure": g_bridge, "bridge": g_bridge,
    "roads": g_road, "rails": g_rails, "canals": g_canal, "boardwalk": g_boardwalk, "cliffclimb": g_ladder,
    "mineshafts": g_pickaxe, "subway": g_train, "wonders": g_crown, "monuments": g_crown, "trade": g_scales, "foodfarms": g_egg,
    "mobfarms": g_skull, "xpfarms": g_skull, "cropfarms": g_wheat, "animalfarms": g_horseshoe,
    "resourcefarms": g_pickaxe,
}


# ------------------------------------------------------------------------------------------------ badges
def shield_pts(x0, y0, x1, y1):
    w, h = x1 - x0, y1 - y0
    pts = [(x0, y0), (x1, y0), (x1, y0 + h * 0.52)]
    for k in range(1, 12):
        t = k / 12
        pts.append((x1 - w / 2 * t, y0 + h * 0.52 + h * 0.48 * math.sin(t * math.pi / 2)))
    pts.append((x0 + w / 2, y1))
    for k in range(11, 0, -1):
        t = k / 12
        pts.append((x0 + w / 2 * t, y0 + h * 0.52 + h * 0.48 * math.sin(t * math.pi / 2)))
    pts.append((x0, y0 + h * 0.52))
    return pts


def badge(pack, size, glyph=None, art=None, disabled=False):
    st = STYLE[pack]
    S = size * 8
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    m = S * 0.04
    rimw = S * (0.065 if size <= 32 else 0.045)
    if st["shape"] == "tile":
        d.rounded_rectangle([m, m, S - m, S - m], radius=S * 0.2, fill=st["rim"])
        d.rounded_rectangle([m + rimw, m + rimw, S - m - rimw, S - m - rimw], radius=S * 0.15, fill=st["fill"])
        inner = (m + rimw, m + rimw, S - m - rimw, S - m - rimw)
    elif st["shape"] == "shield":
        d.polygon(shield_pts(m, m, S - m, S - m), fill=st["rim"])
        d.polygon(shield_pts(m + rimw, m + rimw, S - m - rimw, S - m - rimw * 1.4), fill=st["fill"])
        inner = (m + rimw, m + rimw, S - m - rimw, S - m - rimw * 1.4)
    else:
        d.ellipse([m, m, S - m, S - m], fill=st["rim"])
        d.ellipse([m + rimw, m + rimw, S - m - rimw, S - m - rimw], fill=st["fill"])
        inner = (m + rimw, m + rimw, S - m - rimw, S - m - rimw)
    # soft top light
    hl = Image.new("L", (S, S), 0)
    ImageDraw.Draw(hl).ellipse([S * 0.1, -S * 0.5, S * 0.9, S * 0.45], fill=46)
    mask = Image.new("L", (S, S), 0)
    if st["shape"] == "tile":
        ImageDraw.Draw(mask).rounded_rectangle(inner, radius=S * 0.15, fill=255)
    elif st["shape"] == "shield":
        ImageDraw.Draw(mask).polygon(shield_pts(*inner), fill=255)
    else:
        ImageDraw.Draw(mask).ellipse(inner, fill=255)
    hl = Image.composite(hl, Image.new("L", (S, S), 0), mask)
    img = Image.composite(Image.new("RGBA", (S, S), st["fill2"] + (255,)), img,
                          hl.point(lambda v: 255 if v else 0).filter(ImageFilter.GaussianBlur(S * 0.06))
                          .point(lambda v: v // 2))
    if art:
        art(img, inner, st, mask)
    if glyph:
        small = size <= 32
        pad = (inner[2] - inner[0]) * ((0.09 if small else 0.2) if st["shape"] != "shield" else (0.12 if small else 0.22))
        box = (inner[0] + pad, inner[1] + pad * (0.8 if st["shape"] == "shield" else 1),
               inner[2] - pad, inner[3] - pad * (1.3 if st["shape"] == "shield" else 1))
        side = min(box[2] - box[0], box[3] - box[1])
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        box = (cx - side / 2, cy - side / 2, cx + side / 2, cy + side / 2)
        GLYPHS[glyph](Pen(img, box, st["glyph"] + (255,), st["fill"] + (255,)))
    out = img.resize((size, size), Image.LANCZOS)
    if size <= 32:
        a = out.getchannel("A")
        out = out.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=2))
        out.putalpha(a)
    if disabled:
        g = ImageOps.grayscale(out.convert("RGB")).point(lambda v: int(70 + v * 0.45)).convert("RGBA")
        g.putalpha(out.getchannel("A").point(lambda v: int(v * 0.75)))
        out = g
    return out


# ------------------------------------------------------------------------------------------------ pack emblem art
def vgrad(S, top, bottom):
    g = Image.new("RGBA", (1, S))
    for y in range(S):
        t = y / max(1, S - 1)
        g.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)) + (255,))
    return g.resize((S, S))


def art_neoterra(img, inner, st, mask):
    S = img.size[0]
    sky = vgrad(S, (10, 20, 40), (24, 70, 96))
    img.paste(sky, (0, 0), mask)
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = inner
    w = x1 - x0
    # orbit ring
    d.ellipse([x0 + w * 0.08, y0 + w * 0.30, x1 - w * 0.08, y0 + w * 0.62], outline=st["rim"] + (255,),
              width=int(S * 0.012))
    base = y0 + w * 0.82
    towers = [(0.20, 0.30, 0.42), (0.30, 0.46, 0.18), (0.46, 0.58, 0.06), (0.58, 0.70, 0.26), (0.70, 0.80, 0.40)]
    for a, b, top in towers:
        tx0, tx1, ty = x0 + w * a, x0 + w * b, y0 + w * top
        d.rectangle([tx0, ty, tx1, base], fill=(232, 244, 250, 255))
        for yy in range(int(ty + w * 0.05), int(base - w * 0.02), int(w * 0.045)):
            d.rectangle([tx0 + w * 0.02, yy, tx1 - w * 0.02, yy + w * 0.018], fill=(46, 226, 236, 255))
    d.rectangle([x0 + w * 0.14, base, x1 - w * 0.14, base + w * 0.03], fill=st["rim"] + (255,))
    # glow
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([x0 + w * 0.25, base - w * 0.06, x1 - w * 0.25, base + w * 0.08],
                                 fill=(46, 226, 236, 120))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(S * 0.03)))


def art_hearthwood(img, inner, st, mask):
    S = img.size[0]
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = inner
    w = x1 - x0
    # gold chief band
    chief = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(chief).rectangle([0, 0, S, y0 + w * 0.22], fill=st["rim"] + (255,))
    img.paste(chief, (0, 0), Image.composite(chief.getchannel("A"), Image.new("L", img.size, 0), mask))
    # three oak leaves on the chief
    for k in range(3):                                      # three lozenges on the chief
        cx = x0 + w * (0.3 + 0.2 * k)
        cy = y0 + w * 0.11
        d.polygon([(cx, cy - w * 0.075), (cx + w * 0.045, cy), (cx, cy + w * 0.075), (cx - w * 0.045, cy)],
                  fill=(128, 34, 30, 255))
    # tudor cottage
    cream = st["glyph"] + (255,)
    dark = (60, 34, 22, 255)
    bx0, bx1, by0, by1 = x0 + w * 0.24, x0 + w * 0.76, y0 + w * 0.52, y0 + w * 0.80
    d.polygon([(bx0 - w * 0.06, by0), (x0 + w * 0.5, y0 + w * 0.28), (bx1 + w * 0.06, by0)], fill=(52, 52, 58, 255))
    d.rectangle([bx0, by0, bx1, by1], fill=cream)
    for k in range(5):
        xx = bx0 + (bx1 - bx0) * k / 4
        d.rectangle([xx - w * 0.012, by0, xx + w * 0.012, by1], fill=dark)
    d.rectangle([bx0, by0, bx1, by0 + w * 0.025], fill=dark)
    d.rectangle([x0 + w * 0.45, by1 - w * 0.13, x0 + w * 0.55, by1], fill=dark)
    # chimney with hearth flame
    cx0 = x0 + w * 0.62
    d.rectangle([cx0, y0 + w * 0.30, cx0 + w * 0.07, y0 + w * 0.44], fill=(170, 74, 56, 255))
    flame = [(cx0 + w * 0.035, y0 + w * 0.18), (cx0 + w * 0.07, y0 + w * 0.26), (cx0 + w * 0.05, y0 + w * 0.30),
             (cx0 + w * 0.02, y0 + w * 0.30), (cx0, y0 + w * 0.26)]
    d.polygon(flame, fill=(255, 176, 60, 255))


def art_cascadia(img, inner, st, mask):
    S = img.size[0]
    sky = vgrad(S, (120, 176, 196), (220, 214, 170))
    img.paste(sky, (0, 0), mask)
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = inner
    w = x1 - x0
    # sun
    d.ellipse([x0 + w * 0.62, y0 + w * 0.14, x0 + w * 0.78, y0 + w * 0.30], fill=(250, 214, 120, 255))
    # mountains with snow caps
    peaks = [(0.0, 0.70, 0.32, 0.30, 0.62, 0.70), (0.30, 0.70, 0.62, 0.20, 1.0, 0.70)]
    for a, ay, px, py, b, by in peaks:
        d.polygon([(x0 + w * a, y0 + w * ay), (x0 + w * px, y0 + w * py), (x0 + w * b, y0 + w * by)],
                  fill=(82, 96, 112, 255))
        d.polygon([(x0 + w * (px - 0.08), y0 + w * (py + 0.12)), (x0 + w * px, y0 + w * py),
                   (x0 + w * (px + 0.08), y0 + w * (py + 0.12)), (x0 + w * (px + 0.03), y0 + w * (py + 0.10)),
                   (x0 + w * px, y0 + w * (py + 0.14)), (x0 + w * (px - 0.03), y0 + w * (py + 0.10))],
                  fill=(246, 246, 250, 255))
    # forest floor + river
    ground = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(ground)
    gd.rectangle([0, y0 + w * 0.66, S, S], fill=(38, 84, 52, 255))
    gd.polygon([(x0 + w * 0.44, y0 + w * 0.66), (x0 + w * 0.52, y0 + w * 0.66), (x0 + w * 0.70, S),
                (x0 + w * 0.30, S)], fill=(82, 160, 186, 255))
    img.paste(ground, (0, 0), Image.composite(ground.getchannel("A"), Image.new("L", img.size, 0), mask))
    for fx, fh in ((0.12, 0.30), (0.22, 0.38), (0.78, 0.36), (0.88, 0.28)):
        cx, base = x0 + w * fx, y0 + w * 0.80
        for k in range(3):
            tw = w * (0.10 - 0.025 * k)
            ty = base - fh * w * (0.35 + 0.3 * k)
            d.polygon([(cx - tw, ty + w * 0.12), (cx, ty - w * 0.04), (cx + tw, ty + w * 0.12)], fill=(24, 60, 38, 255))
        d.rectangle([cx - w * 0.012, base - w * 0.02, cx + w * 0.012, base + w * 0.03], fill=(92, 60, 34, 255))


def art_farmworks(img, inner, st, mask):
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = inner
    w = x1 - x0
    red = st["accent"] + (255,)
    # barn
    d.polygon([(x0 + w * 0.18, y0 + w * 0.50), (x0 + w * 0.30, y0 + w * 0.30), (x0 + w * 0.50, y0 + w * 0.22),
               (x0 + w * 0.70, y0 + w * 0.30), (x0 + w * 0.82, y0 + w * 0.50)], fill=(70, 40, 24, 255))
    d.rectangle([x0 + w * 0.22, y0 + w * 0.48, x0 + w * 0.78, y0 + w * 0.82], fill=red)
    d.rectangle([x0 + w * 0.40, y0 + w * 0.58, x0 + w * 0.60, y0 + w * 0.82], fill=(246, 232, 200, 255))
    d.line([(x0 + w * 0.40, y0 + w * 0.58), (x0 + w * 0.60, y0 + w * 0.82)], fill=red, width=int(w * 0.03))
    d.line([(x0 + w * 0.60, y0 + w * 0.58), (x0 + w * 0.40, y0 + w * 0.82)], fill=red, width=int(w * 0.03))
    # gear
    gx, gy, r = x0 + w * 0.80, y0 + w * 0.22, w * 0.11
    for k in range(8):
        a = k * math.pi / 4
        d.rectangle([gx + math.cos(a) * r - w * 0.025, gy + math.sin(a) * r - w * 0.025,
                     gx + math.cos(a) * r + w * 0.025, gy + math.sin(a) * r + w * 0.025], fill=(84, 48, 22, 255))
    d.ellipse([gx - r * 0.85, gy - r * 0.85, gx + r * 0.85, gy + r * 0.85], fill=(84, 48, 22, 255))
    d.ellipse([gx - r * 0.35, gy - r * 0.35, gx + r * 0.35, gy + r * 0.35], fill=st["fill"] + (255,))
    # wheat sheaf
    for k, dx in enumerate((-0.04, 0, 0.04)):
        bx = x0 + w * (0.16 + dx)
        d.line([(x0 + w * 0.16, y0 + w * 0.82), (bx, y0 + w * 0.36)], fill=(120, 80, 30, 255), width=int(w * 0.02))
        for j in range(4):
            yy = y0 + w * (0.36 + 0.06 * j)
            d.ellipse([bx - w * 0.03, yy, bx + w * 0.03, yy + w * 0.05], fill=(150, 104, 36, 255))


ART = {"Neoterra": art_neoterra, "Hearthwood": art_hearthwood, "Cascadia": art_cascadia, "Farmworks": art_farmworks}


def emblem(pack, size):
    return badge(pack, size, art=ART[pack])


# ------------------------------------------------------------------------------------------------ mod logo / banner
def text_center(d, xy, text, font, fill, shadow=None, spacing=0):
    x, y = xy
    if spacing:
        widths = [d.textlength(ch, font=font) for ch in text]
        total = sum(widths) + spacing * (len(text) - 1)
        cx = x - total / 2
        for ch, wch in zip(text, widths):
            if shadow:
                d.text((cx + 4, y + 4), ch, font=font, fill=shadow)
            d.text((cx, y), ch, font=font, fill=fill)
            cx += wch + spacing
        return
    tw = d.textlength(text, font=font)
    if shadow:
        d.text((x - tw / 2 + 4, y + 4), text, font=font, fill=shadow)
    d.text((x - tw / 2, y), text, font=font, fill=fill)


def mod_logo(W=1200, H=420, bg=None):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)) if bg is None else bg.copy()
    d = ImageDraw.Draw(img)
    e = int(H * 0.46)
    packs = ["Hearthwood", "Neoterra", "Cascadia"]
    for k, p in enumerate(packs):
        em = emblem(p, e)
        x = int(W / 2 + (k - 1) * e * 1.08 - e / 2)
        img.alpha_composite(em, (x, int(H * 0.04)))
    f1 = ImageFont.truetype(FONT_SANS, int(H * 0.25))
    f2 = ImageFont.truetype(FONT_SANS, int(H * 0.085))
    text_center(d, (W / 2, H * 0.52), "NEOTERRA", f1, (236, 248, 252, 255), shadow=(10, 20, 30, 200),
                spacing=int(H * 0.03))
    text_center(d, (W / 2, H * 0.80), "STYLE PACKS FOR MINECOLONIES", f2, (46, 226, 236, 255), shadow=(10, 20, 30, 200),
                spacing=int(H * 0.012))
    return img


def banner(collage_dir, W=1920, H=1080):
    bg = vgrad(max(W, H), (12, 24, 40), (30, 62, 86)).resize((W, H))
    shots = sorted(Path(collage_dir).glob("*.png")) if collage_dir and Path(collage_dir).exists() else []
    if shots:
        cols = 4
        tw, th = W // cols, H // 2
        for i, sp in enumerate(shots[:8]):
            im = Image.open(sp).convert("RGBA")
            px = im.load()
            for yy in range(im.height):                      # knock out the renderer's flat background
                for xx in range(im.width):
                    r, g, b, a = px[xx, yy]
                    if abs(r - 236) < 6 and abs(g - 240) < 6 and abs(b - 244) < 6:
                        px[xx, yy] = (0, 0, 0, 0)
            im = im.crop(im.getbbox())
            im.thumbnail((int(tw * 0.92), int(th * 0.92)))
            bg.alpha_composite(im, ((i % cols) * tw + (tw - im.width) // 2, (i // cols) * th + (th - im.height) // 2))
        veil = Image.new("RGBA", (W, H), (8, 16, 28, 110))
        bg.alpha_composite(veil)
        scrim = Image.new("L", (W, H), 0)
        ImageDraw.Draw(scrim).ellipse([W * 0.12, H * 0.18, W * 0.88, H * 0.82], fill=235)
        scrim = scrim.filter(ImageFilter.GaussianBlur(W * 0.06))
        bg.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), v) for v in (8, 16, 28)], scrim)))
    logo = mod_logo(int(W * 0.7), int(W * 0.7 * 0.35))
    bg.alpha_composite(logo, ((W - logo.width) // 2, (H - logo.height) // 2))
    return bg


DESC = {
    "Neoterra": "Modern city: white and grey concrete, glass, roof gardens and coloured accents. Every building is "
                "hand-designed, vanilla blocks only, and grows from a compact level-1 hut into a full complex by level 5.",
    "Hearthwood": "English village: brick, plaster and dark timber framing, slate and clay-tile roofs, chimneys, flower "
                  "boxes and gardens. Hand-designed, vanilla blocks only, every building grows into a full complex by "
                  "level 5.",
    "Cascadia": "Pacific Northwest timber town: log and board-and-batten walls, river-rock footings, dark shake roofs, "
                "porches and lookouts. Hand-designed, vanilla blocks only, every building grows into a full complex by "
                "level 5.",
}


# ------------------------------------------------------------------------------------------------ main
def main():
    packs = {"Neoterra": "neoterra.png", "Hearthwood": "hearthwood.png", "Cascadia": "cascadia.png",
             "Farmworks": "farmworks.png"}
    n = 0
    sheet_rows = []
    for pack, logo in packs.items():
        root = ROOT / "stylepacks" / pack
        if not root.exists():
            continue
        emblem(pack, 128).save(root / logo)
        if pack in DESC and (root / "pack.json").exists():
            import json
            meta = json.loads((root / "pack.json").read_text())
            meta["desc"] = DESC[pack]
            (root / "pack.json").write_text(json.dumps(meta, indent=2) + "\n")
        row = [emblem(pack, 96)]
        for folder in sorted(p for p in root.rglob("*") if p.is_dir()):
            key = folder.name
            if key not in GLYPHS:
                print(f"no glyph for {pack}/{folder.relative_to(root)}")
                continue
            badge(pack, 20, key).save(folder / "icon.png")
            badge(pack, 20, key, disabled=True).save(folder / "icon_disabled.png")
            row.append(badge(pack, 48, key))
            n += 1
        sheet_rows.append((pack, row))
    out = ROOT / "docs" / "branding"
    out.mkdir(parents=True, exist_ok=True)
    # overview sheet
    W = max(len(r) for _, r in sheet_rows) * 56 + 140
    sheet = Image.new("RGBA", (W, 110 * len(sheet_rows)), (240, 242, 246, 255))
    d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype(FONT_SANS, 16)
    for i, (pack, row) in enumerate(sheet_rows):
        y = i * 110
        d.text((8, y + 6), pack, font=f, fill=(20, 20, 20, 255))
        sheet.alpha_composite(row[0], (8, y + 10))
        for k, im in enumerate(row[1:]):
            sheet.alpha_composite(im, (120 + k * 56, y + 40))
    sheet.save(out / "icons_overview.png")
    logo = mod_logo()
    logo.save(out / "logo.png")
    res = ROOT / "mod" / "src" / "main" / "resources"
    if res.exists():
        mod_logo(800, 280).save(res / "neoterra_logo.png")
    sq = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
    big = emblem("Neoterra", 400)
    sq.alpha_composite(big)
    sq.save(out / "icon_square.png")
    banner(out / "shots").convert("RGB").save(out / "banner.png")
    print(f"branding: 4 pack logos, {n} category icons (+ disabled), mod logo, banner -> {out}")


if __name__ == "__main__":
    main()
