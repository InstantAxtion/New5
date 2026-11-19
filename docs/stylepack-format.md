# MineColonies style pack format (NeoForge 1.21.1)

Notes taken from the official packs in `ldtteam/minecolonies` branch `version/1.21`
(`src/main/resources/blueprints/minecolonies/<pack>/`) and Structurize's `BlueprintUtil`.

## Install location
`.minecraft/blueprints/<PackFolder>/pack.json` – each folder with a `pack.json` is one pack.

## pack.json
```json
{
  "icon": "mypack.png",
  "name": "Display Name",
  "authors": ["..."],
  "desc": "...",
  "mods": ["structurize", "minecolonies"],
  "version": "1",
  "pack-format": "1"
}
```
`icon` is relative to the pack folder. `pack-format` must be 1. Every mod in `mods` must be loaded or the pack is skipped.

## Folder layout (same categories as the official packs)
Each category folder has `icon.png` + `icon_disabled.png` for the Build Tool tabs.
```
fundamentals/    townhall builder residence cook(=restaurant) lumberjack miner tavern hospital
agriculture/horticulture/  farmer florist plantation composter
agriculture/husbandry/     beekeeper chickenherder cowboy fisherman rabbithutch shepherd swineherder
agriculture/fields/        (field decorations)
craftsmanship/carpentry/   sawmill fletcher
craftsmanship/luxury/      alchemist baker concretemixer cookery dyer glassblower
craftsmanship/masonry/     crusher sifter stonemason stonesmeltery
craftsmanship/metallurgy/  blacksmith mechanic smeltery
craftsmanship/storage/     warehouse deliveryman courier
education/       library school university communitycollege
military/        barracks barrackstower guardtower archery combatacademy gatehouse stable
mystic/          enchanter graveyard mysticalsite netherworker
infrastructure/  roads, bridges, mineshafts (miner shafts), rails, ...
decorations/     anything without a hut
walls/           wall pieces
```
Hut buildings: `<hutname>1.blueprint` … `<hutname>5.blueprint` (one per upgrade level;
some huts have fewer levels, e.g. warehouse/townhall all 5, guard tower etc. vary).

## Blueprint NBT (hut levels)
- `mcversion` = 3955 (1.21.1), `required_mods` = `["minecolonies"]` when a hut block is used.
- `name` = file name, e.g. `builder1.blueprint`.
- Palette holds `minecolonies:blockhut<name>[facing=...]`, plus often
  `structurize:blocksolidsubstitution` (builder fills with local ground block) and
  `structurize:blocksubstitution` (leave whatever is in the world).
- `primary_offset` = position of the hut block inside the blueprint.
- The hut block's block entity (`id: minecolonies:colonybuilding`) carries
  `blueprintDataProvider`:
  - `corner1` / `corner2`: blueprint corners relative to the hut block
  - `path`: e.g. `fundamentals/builder1.blueprint`, `schematicName`: `builder1`
  - `posTagMap`: list of `{tagPos (relative to hut), tagNameList:[{tagName}]}`
    – `groundlevel` tag marks the ground height used when placing,
    other tags are building specific (e.g. `stand_out`, work spots).
- Racks are `minecolonies:blockminecoloniesrack` with block entity `minecolonies:rack`.

## Child huts (multi-hut buildings)
Any hut block inside a building's blueprint is registered as a child of that building when the
builder places it (`AbstractBuildingContainer#registerBlockPosition` -> `setParent`). The official
barracks do this with `barrackstower`. A child hut's block entity stores `path` =
`<category>/<name>0.blueprint` (level 0, corners 0,0,0); upgrading it builds `<name>1..5` at the
child's position. The parent uses `structurize:blocksubstitution` in the child's volume so the two
never overwrite each other. A residence holds `level` residents (max 5) per hut.

## Decorations
No hut: the anchor is `minecolonies:decorationcontroller[facing,mirror,waterlogged]` with block entity
`minecolonies:decorationcontroller` {path, name, pack, mirror, rotation, blueprintDataProvider}.
The tag `invisible` hides a blueprint from the Build Tool list.
