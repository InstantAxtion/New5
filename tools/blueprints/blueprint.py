"""
Minimal writer/reader for Structurize `.blueprint` files (format version 1).

Format verified against Structurize source:
  com.ldtteam.structurize.blueprints.v1.BlueprintUtil#writeBlueprintToNBT / readBlueprintFromNBT

Layout (gzipped NBT compound):
  version        byte   = 1
  size_x/y/z     short
  palette        list<compound{Name, Properties?}>   (index 0 is always minecraft:air)
  blocks         int[]  palette indices as shorts, ordered y -> z -> x, packed two per int (hi, lo)
  tile_entities  list<compound>  (each with x/y/z shorts relative to blueprint origin)
  entities       list<compound>
  required_mods  list<string>
  name           string
  architects     list<string>
  mcversion      int    (data version; Structurize runs Mojang's DataFixers from here on load)
  optional_data  {structurize: {primary_offset: {x,y,z}}}
"""
from __future__ import annotations

import gzip
import io

import nbtlib
from nbtlib import tag as T

AIR = "minecraft:air"
DATA_VERSION_1_21_1 = 3955  # MineColonies 1.21.1 packs are saved with this


def parse_state(state: str) -> tuple[str, dict[str, str]]:
    """'minecraft:oak_stairs[facing=north,half=bottom]' -> (name, props)."""
    if "[" in state:
        name, rest = state.split("[", 1)
        props = dict(kv.split("=", 1) for kv in rest.rstrip("]").split(",") if kv)
    else:
        name, props = state, {}
    if ":" not in name:
        name = "minecraft:" + name
    return name, props


def format_state(name: str, props: dict[str, str]) -> str:
    if not props:
        return name
    return name + "[" + ",".join(f"{k}={v}" for k, v in sorted(props.items())) + "]"


class Blueprint:
    def __init__(self, sx: int, sy: int, sz: int, name: str):
        self.sx, self.sy, self.sz = sx, sy, sz
        self.name = name
        # grid[y][z][x] -> canonical state string
        self.grid = [[[AIR] * sx for _ in range(sz)] for _ in range(sy)]
        self.primary_offset = (0, 0, 0)
        self.architects: list[str] = []
        # (x, y, z) -> block entity compound (x/y/z are added on save)
        self.tile_entities: dict[tuple[int, int, int], nbtlib.Compound] = {}

    # ---- editing helpers -------------------------------------------------
    def inside(self, x, y, z):
        return 0 <= x < self.sx and 0 <= y < self.sy and 0 <= z < self.sz

    def set(self, x, y, z, state: str, te: nbtlib.Compound | None = None):
        """Place a block. Overwriting a block also drops its old block entity."""
        if not self.inside(x, y, z):
            raise IndexError(f"({x},{y},{z}) outside {self.sx}x{self.sy}x{self.sz}")
        self.grid[y][z][x] = format_state(*parse_state(state))
        if te is None:
            self.tile_entities.pop((x, y, z), None)
        else:
            self.tile_entities[(x, y, z)] = te

    def get(self, x, y, z) -> str:
        if not self.inside(x, y, z):
            return AIR
        return self.grid[y][z][x]

    def fill(self, x1, y1, z1, x2, y2, z2, state: str, te_factory=None):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            for z in range(min(z1, z2), max(z1, z2) + 1):
                for x in range(min(x1, x2), max(x1, x2) + 1):
                    self.set(x, y, z, state, te_factory() if te_factory else None)

    def blocks(self):
        for y in range(self.sy):
            for z in range(self.sz):
                for x in range(self.sx):
                    yield x, y, z, self.grid[y][z][x]

    # ---- serialization ---------------------------------------------------
    def to_nbt(self) -> nbtlib.Compound:
        palette = [AIR]
        index = {AIR: 0}
        flat = []
        for y in range(self.sy):
            for z in range(self.sz):
                for x in range(self.sx):
                    s = self.grid[y][z][x]
                    if s not in index:
                        index[s] = len(palette)
                        palette.append(s)
                    flat.append(index[s])
        if len(palette) > 32767:
            raise ValueError("palette too large")

        ints = []
        for i in range(0, len(flat), 2):
            hi = flat[i]
            lo = flat[i + 1] if i + 1 < len(flat) else 0
            v = (hi << 16) | (lo & 0xFFFF)
            if v >= 2**31:
                v -= 2**32
            ints.append(v)

        pal_tags = []
        for s in palette:
            n, props = parse_state(s)
            c = T.Compound({"Name": T.String(n)})
            if props:
                c["Properties"] = T.Compound({k: T.String(v) for k, v in props.items()})
            pal_tags.append(c)

        return T.Compound({
            "version": T.Byte(1),
            "size_x": T.Short(self.sx),
            "size_y": T.Short(self.sy),
            "size_z": T.Short(self.sz),
            "palette": T.List[T.Compound](pal_tags),
            "blocks": T.IntArray(ints),
            "tile_entities": T.List[T.Compound](self._te_list()),
            "entities": T.List[T.Compound]([]),
            "required_mods": T.List[T.String](sorted({
                parse_state(s)[0].split(":")[0] for s in palette
            } - {"minecraft", "structurize"})),
            "name": T.String(self.name),
            "architects": T.List[T.String]([T.String(a) for a in self.architects]),
            "mcversion": T.Int(DATA_VERSION_1_21_1),
            "optional_data": T.Compound({
                "structurize": T.Compound({
                    "primary_offset": T.Compound({
                        "x": T.Int(self.primary_offset[0]),
                        "y": T.Int(self.primary_offset[1]),
                        "z": T.Int(self.primary_offset[2]),
                    })
                })
            }),
        })

    def _te_list(self):
        out = []
        for (x, y, z), te in sorted(self.tile_entities.items(), key=lambda kv: (kv[0][1], kv[0][2], kv[0][0])):
            c = T.Compound(dict(te))
            c["x"], c["y"], c["z"] = T.Short(x), T.Short(y), T.Short(z)
            out.append(c)
        return out

    def save(self, path):
        f = nbtlib.File(self.to_nbt(), gzipped=True)
        f.save(path)


def load(path) -> Blueprint:
    """Read a .blueprint back (used for verification / converting existing files)."""
    root = nbtlib.load(path)
    if int(root["version"]) != 1:
        raise ValueError("unsupported blueprint version")
    sx, sy, sz = int(root["size_x"]), int(root["size_y"]), int(root["size_z"])
    bp = Blueprint(sx, sy, sz, str(root.get("name", "")))
    palette = []
    for c in root["palette"]:
        props = {k: str(v) for k, v in c.get("Properties", {}).items()}
        palette.append(format_state(str(c["Name"]), props))
    shorts = []
    for v in root["blocks"]:
        v = int(v) & 0xFFFFFFFF
        shorts += [(v >> 16) & 0xFFFF, v & 0xFFFF]
    i = 0
    for y in range(sy):
        for z in range(sz):
            for x in range(sx):
                bp.grid[y][z][x] = palette[shorts[i]]
                i += 1
    for te in root.get("tile_entities", []):
        bp.tile_entities[(int(te["x"]), int(te["y"]), int(te["z"]))] = te
    po = root.get("optional_data", {}).get("structurize", {}).get("primary_offset")
    if po is not None:
        bp.primary_offset = (int(po["x"]), int(po["y"]), int(po["z"]))
    return bp
