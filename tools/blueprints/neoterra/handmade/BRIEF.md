# Hand-made hut designs – designer brief

The user's verdict on the old generated buildings: *"buildings don't look like what they are supposed to represent and
random blocks are placed inside buildings instead of true decorations"*, *"stick to vanilla blocks"*, *"get light
inspiration from how the built-in themes are done"*. Your job is to fix that for your hut types by designing each one
by hand – like a skilled MineColonies builder would – for three style packs and every level.

## What "good" means here

1. **It reads as what it is from the street.** A bakery has a shop front, a big oven chimney, maybe a striped awning
   and bread on the counter. A blacksmith has an open-sided forge with a glowing hearth, anvil out front, a quench
   trough. A library has tall windows and a reading room. Ask yourself: if someone saw only the outside, would they
   guess the building? Use real-world references for the building type in that pack's style.
2. **Every interior block has a purpose.** Rooms are laid out like the real thing: counters with stools, tables
   with chairs around them, beds with nightstands, kitchens with stove/sink/counters, workshops with workbenches
   and tool walls, shelves against walls, lighting overhead. No scattered stairs/logs/slabs "as furniture" filling
   random wall spots. Fewer, well-placed pieces beat many random ones.
3. **Vanilla blocks only**, plus the MineColonies blocks the toolkit gives you (hut block, rack, composted dirt,
   named grave, minecolonies barrel_block where required) and `domum_ornamentum:architectscutter` only where the
   builder's requirements list it. No other Domum Ornamentum blocks.
4. **Proper construction:** closed walls (no gaps), gable ends filled, roofs that cover the building with a small
   overhang, chimneys that go through the roof, doors that open onto floor, stairs/ladders that actually connect
   floors with headroom (2 free blocks above every walkable cell), no floating bits, nothing poking out of the plot.
5. **Size like the built-in packs:** most huts 11–25 blocks wide; big civic buildings up to ~31. Plot max 33×33.
   The plot is reserved at level 1 for the level-5 size (a later script pads every level to the biggest one), so
   don't waste space – grow sensibly.

## The three packs (each must be clearly different in footprint, silhouette, roof, materials, and props)

| Pack | Character | Typical materials | Roofs / form |
|---|---|---|---|
| **Neoterra** | modern / near-future city: clean lines, glass, terraces, planters, signage with glowing text | white & light-gray concrete, smooth quartz, polished diorite/andesite, glass & gray-stained panes, birch & mangrove wood accents, cyan terracotta/concrete accents, sea lanterns, end rods | flat roofs with parapets, roof terraces, cantilevers, canopies, glass curtain walls, solar/greenery on roofs |
| **Hearthwood** | English village / Tudor & Cotswold: cosy, crafted | stone-brick or brick plinth, calcite or white-plaster walls with dark-oak timber framing, bricks, oak/dark-oak, deepslate-tile roofs, leaded windows (panes), flower boxes, hanging signs | steep gables, cross-gables, jettied upper floors, dormers, big brick chimneys, cottage gardens with fences |
| **Cascadia** | Pacific-Northwest logging / mountain town: rugged timber | spruce logs (corner posts, horizontal log walls), stripped spruce, spruce & dark-oak planks, river-rock footing (cobble / mossy cobble / andesite / tuff), dark roofs (spruce/dark-oak or deepslate), moss, lanterns, barrels, hay | steep A-frames and long gables, deep covered porches/decks, false fronts, lean-tos, stone chimneys, rail fences. Use contrast (dark trim vs light stripped logs, stone vs wood) – avoid one flat brown mass |

Give each pack a *different* layout for the same hut type (not the same box re-skinned): different footprint size and
proportions, different roof form, different storey count/arrangement. A checker flags pairs whose size, palette or
shape are too alike across packs.

## Levels 1–5 (taverns 1–3, some huts 1–3)

MineColonies upgrades a building in place: **the hut block must be at the same position relative to the building on
every level**, and each level should look like the same building grown: L1 a modest core that already works and
looks finished, then extensions, a second storey, wings, porches/yards, nicer materials and more decoration. Keep
the same plot size (`Design(..., size=...)`) across levels of a type within a pack.

## Requirements (MUST be met – Design.finish() raises otherwise)

`requirements.json` lists, per pack-relative path (e.g. `fundamentals/tavern3.blueprint`), the minimum number of
beds, racks, work blocks (`items`), seats (`sit` tags → use `d.chair(..., sit=True)`), tagged work spots
(`d.spot(x, y, z, "work")` – tag goes on the floor under a standing cell), bookshelves (`d.bookshelf`), composted
dirt (`d.floor_item`), outdoor fixtures (`d.yard_item` / `d.grave`) and for fisherman / plantation / miner /
netherworker / concretemixer a functional **cluster** you must paste unchanged with `d.cluster(x0, z0)` (size via
`d.cluster_size()`; ground aligned automatically; plan your building around it). Use `d.item(...)` for every
required work block so it is counted; decorative copies (e.g. kegs) use plain `d.set` / `d.keg`.
Everything required must be reachable on foot (walk-check), including beds (one half) and racks.

Read the per-level numbers before designing:
`python3 -c "import json;r=json.load(open('requirements.json'));[print(k,v) for k,v in sorted(r.items()) if v['base']=='baker']"`

Big rack counts (warehouse, builder, deliveryman…) should look like real storage: aisles of rack shelving 3 high
with walkways, loading doors, not racks stuffed in random holes.

## Toolkit (read hm.py – it is short)

`Design(pack, rel, size, gy=1, paving=...)` → helpers `set/fill/clear/box/layer` (ASCII plans), `door/double_door/
window`, roofs `gable/hip/flat`, furniture `chair/table/dining/seating/bed/rack/item/keg/counter/hearth/lamp/
wall_torch/plant/candle/rug/sign/banner/bookshelf`, game `hut/tag/spot/cluster/yard_item/grave/floor_item`.
North (z=0) is the street/entrance side. Ground surface at y=gy (1); first walkable layer y=2. Read the facing
conventions at the top of hm.py. Register your types with `@design("baker")` returning the *unfinished* Design.

Reference design: `designs/tavern.py` (one function per pack; levels handled with parameters). Match or beat it.

## Workflow (iterate visually – at least two rounds per type)

```
cd tools/blueprints/neoterra/handmade
python3 preview.py <your scratch dir> baker florist --levels=1,3,5
```
It builds every pack × level, prints requirement errors, invalid block states and unreachable blocks, and writes
`<dir>/<type>.png` (per row: street view, back view, then a cutaway per floor) plus single images in `<dir>/img/`.
**Look at the images** (Read tool) – especially the cutaways – fix what looks wrong, repeat. The renderer draws
stairs, slabs, fences, panes, doors, carpets, lanterns etc. with their real shapes but colours are approximate.

For light inspiration you can render the built-in MineColonies packs (23 styles, e.g. medievaloak, colonial,
nordic, shire, caledonia, fortress, lostcity, spacewars) from
`/tmp/claude-0/-home-user-New5/d6177730-cb9f-5d18-81bb-de5acb2fa842/scratchpad/mc/blueprints/minecolonies/<style>/...`
with `python3 ../../render.py <file.blueprint> <out prefix>`. Inspiration only – never copy their geometry.

## Rules for working in the shared repo

* Write ONLY your own file `designs/<your group>.py` (and files in your own scratch dir). Do not edit hm.py,
  preview.py, other designs, or anything under `stylepacks/`. If you need a helper, define it in your file.
* Don't commit or push; the coordinator integrates.
* Done = every type in your group builds for all 3 packs and all levels with no errors, no bad states, nothing
  unreachable, and you have looked at the renders and are happy a player would recognise each building.

## Round 2: compound structures (barracks, gatehouse, wall guard tower, sky tower, bunker, twin builder, grand projects)

Same rules as above, plus:

* **Child huts.** Some structures contain child huts that MineColonies builds from their own blueprint:
  barracks → `barrackstower`, skytower → `skytowerflat`, bunker → `bunkerkitchen` / `bunkerclinic` /
  `bunkerschool` / `bunkerfarm`, twinbuilder → `twinbuilderannex`, cathedral/colossus/grandbridge/royalgranary →
  `<name>wing`. requirements.json lists for every parent level the exact number of each child
  (`children: [{hut, path, count}]`) and every child level has its own requirements (`child: true`).
  - In the parent: reserve the child's space with `d.reserve(x1,y1,z1,x2,y2,z2)` and place the child hut with
    `d.child_hut(x, y, z, "military/barrackstower0.blueprint")`.
  - Write the child as its own design (`@design("barrackstower")`). Parent level L is assembled with child
    level L: the child blueprint is pasted so that its hut block lands on the parent's child-hut cell. So the
    child's footprint around its hut must fit the reserved box exactly. Share the geometry as constants between
    the parent and child functions.
  - Child designs normally use `gy=0` with the hut at y=1, i.e. the child's y=0 sits on the parent's ground layer.
  - preview.py shows and walk-checks the ASSEMBLED parent; children are not walk-checked on their own.
* **Special tags** (`tagreq`): the gatehouse needs `gate`, `knight` and `archer` tags. Read
  `../military_real.py` and the current `stylepacks/*/military/gatehouse*.blueprint` to see where they go:
  gate tags on the ground under the gate opening, knight posts on the ground beside it, archers on the wall walk.
  The bunker kitchen needs `work` tags; use `d.tag(...)` / `d.spot(...)` as appropriate.
* **Grand projects** use this mod's hut blocks (`neoterra:blockhutcathedral` etc. and `neoterra:blockhutwonderwing`
  for the wings); the self-test requires exactly 2 wing huts in every grand project level. They are real-world
  landmarks: big, ornate, a skyline piece – not a box.
* **Bunker** is underground: its `gy` (ground surface) is high (see requirements `gy`, e.g. 24). Rooms are
  below ground, with an entrance building / hatch at the surface. Cutaways of underground floors aren't
  drawn automatically. Render your own slices with `render.iso(preview.cut(bp, y), ...)` to look inside.
* Look at the current versions (`stylepacks/<pack>/...`) only to understand requirements and child alignment.
  Your designs replace them completely.
