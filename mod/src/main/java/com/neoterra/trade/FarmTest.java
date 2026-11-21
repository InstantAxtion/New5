package com.neoterra.trade;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.ldtteam.structurize.blueprints.v1.Blueprint;
import com.ldtteam.structurize.storage.StructurePacks;
import com.ldtteam.structurize.util.BlockInfo;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.Container;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Development farm test, only active with -Dneoterra.farmtest=true (gradle runFarmtest): builds every Farmworks
 * farm listed in data/neoterra/farmtests.json from its blueprint, loads the player inputs, spawns the mobs the
 * player would bring, random-ticks growing blocks (10x the default rate - random ticks need a real player nearby,
 * a dedicated test server has none), runs the farms and checks the items in their output containers.
 */
final class FarmTest
{
    private static final int SPACING = 64;
    private static final int BASE_Y = 140;

    private final List<Farm> farms = new ArrayList<>();
    private int tick = 0;
    private int stage = 0;
    private int runTicks = 0;
    private int maxTicks = 0;
    private final RandomSource random = RandomSource.create(1234);

    private static final class Farm
    {
        String rel;
        JsonObject spec;
        BlockPos origin;        // world position of blueprint (0,0,0)
        BlockPos anchor;        // world position of the controller
        int sx, sy, sz;
        int ticks;
        final List<BlockPos> randomTicking = new ArrayList<>();
        boolean built;
        String error;
    }

    static void register()
    {
        if (Boolean.getBoolean("neoterra.farmtest"))
        {
            NeoForge.EVENT_BUS.register(new FarmTest());
        }
    }

    @SubscribeEvent
    public void onTick(final ServerTickEvent.Post event)
    {
        tick++;
        if (tick < 60 || stage < 0)
        {
            return;
        }
        final ServerLevel level = event.getServer().overworld();
        try
        {
            switch (stage)
            {
                case 0 -> { setup(level); stage = 1; }
                case 1 -> { build(level); stage = 2; }
                case 2 -> { start(level); stage = 3; }
                case 3 ->
                {
                    runTicks++;
                    randomTicks(level);
                    if (runTicks % 1200 == 0)
                    {
                        log("%d / %d ticks", runTicks, maxTicks);
                    }
                    if (runTicks >= maxTicks)
                    {
                        finish(level, check(level));
                    }
                }
                default -> { }
            }
        }
        catch (final Throwable t)
        {
            NeoterraTrade.LOG.error("FARMTEST FAIL (exception in stage " + stage + ")", t);
            finish(level, false);
        }
    }

    private void setup(final ServerLevel level) throws Exception
    {
        final JsonObject root;
        try (InputStream in = FarmTest.class.getResourceAsStream("/data/neoterra/farmtests.json"))
        {
            if (in == null)
            {
                throw new IllegalStateException("data/neoterra/farmtests.json missing");
            }
            root = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
        }
        final String only = System.getProperty("neoterra.farmtest.only", "");
        int i = 0;
        for (final Map.Entry<String, JsonElement> e : root.getAsJsonObject("farms").entrySet())
        {
            if (!only.isEmpty() && !e.getKey().contains(only))
            {
                continue;
            }
            final Farm f = new Farm();
            f.rel = e.getKey();
            f.spec = e.getValue().getAsJsonObject();
            f.ticks = f.spec.has("ticks") ? f.spec.get("ticks").getAsInt() : 6000;
            f.anchor = new BlockPos(1000 + (i % 6) * SPACING, BASE_Y, 1000 + (i / 6) * SPACING);
            farms.add(f);
            maxTicks = Math.max(maxTicks, f.ticks);
            i++;
        }
        level.setDayTime(1000);
        log("%d farms to test, %d ticks", farms.size(), maxTicks);
    }

    private void build(final ServerLevel level)
    {
        for (final Farm f : farms)
        {
            final Blueprint bp = StructurePacks.getBlueprint(root(), f.rel, level.registryAccess());
            if (bp == null)
            {
                f.error = "blueprint did not load";
                continue;
            }
            final BlockPos po = bp.getPrimaryBlockOffset();
            f.origin = f.anchor.subtract(po);
            f.sx = bp.getSizeX();
            f.sy = bp.getSizeY();
            f.sz = bp.getSizeZ();
            for (int cx = (f.origin.getX() - 16) >> 4; cx <= (f.origin.getX() + f.sx + 16) >> 4; cx++)
            {
                for (int cz = (f.origin.getZ() - 16) >> 4; cz <= (f.origin.getZ() + f.sz + 16) >> 4; cz++)
                {
                    level.setChunkForced(cx, cz, true);
                    level.getChunk(cx, cz);
                }
            }
            // clear the box (and a margin) to air, a stone slab of ground under it
            for (int x = -4; x < f.sx + 4; x++)
            {
                for (int z = -4; z < f.sz + 4; z++)
                {
                    for (int y = -1; y < f.sy + 6; y++)
                    {
                        level.setBlock(f.origin.offset(x, y, z), y < 0 ? Blocks.STONE.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2 | 16);
                    }
                }
            }
            // pass 1: blocks that stand on their own; pass 2: everything attached, redstone, fluids
            final List<BlockInfo> later = new ArrayList<>();
            for (final BlockInfo info : bp.getBlockInfoAsList())
            {
                final BlockState st = resolve(info.getState());
                if (st == null)
                {
                    continue;
                }
                if (st.isCollisionShapeFullBlock(level, BlockPos.ZERO) && st.getFluidState().isEmpty())
                {
                    level.setBlock(f.origin.offset(info.getPos()), st, 2 | 16);
                }
                else
                {
                    later.add(info);
                }
            }
            for (final BlockInfo info : later)
            {
                level.setBlock(f.origin.offset(info.getPos()), resolve(info.getState()), 2 | 16);
            }
            // then let everything update once, as after a builder finishes
            for (final BlockInfo info : bp.getBlockInfoAsList())
            {
                final BlockPos p = f.origin.offset(info.getPos());
                final BlockState st = level.getBlockState(p);
                level.sendBlockUpdated(p, st, st, 3);
                level.updateNeighborsAt(p, st.getBlock());
                if (!st.getFluidState().isEmpty())
                {
                    level.scheduleTick(p, st.getFluidState().getType(), 1);
                }
                if (st.isRandomlyTicking())
                {
                    f.randomTicking.add(p);
                }
            }
            f.built = true;
        }
        log("built %d farms", farms.stream().filter(x -> x.built).count());
    }

    private static String root()
    {
        return "Farmworks";
    }

    /** Structurize substitution blocks: solid substitution = the ground (stone), the others = leave as is (air). */
    private static BlockState resolve(final BlockState st)
    {
        final String id = BuiltInRegistries.BLOCK.getKey(st.getBlock()).toString();
        if (id.equals("structurize:blocksolidsubstitution"))
        {
            return Blocks.STONE.defaultBlockState();
        }
        if (id.startsWith("structurize:"))
        {
            return null;
        }
        if (id.equals("minecolonies:decorationcontroller"))
        {
            return Blocks.STONE_BRICKS.defaultBlockState();
        }
        return st;
    }

    private void start(final ServerLevel level)
    {
        for (final Farm f : farms)
        {
            if (!f.built)
            {
                continue;
            }
            final JsonObject inputs = f.spec.getAsJsonObject("inputs");
            if (inputs != null)
            {
                for (final Map.Entry<String, JsonElement> e : inputs.entrySet())
                {
                    final BlockPos p = f.anchor.offset(rel(e.getKey()));
                    final BlockEntity be = level.getBlockEntity(p);
                    if (!(be instanceof Container c))
                    {
                        f.error = "input at " + e.getKey() + " is not a container (" + level.getBlockState(p) + ")";
                        continue;
                    }
                    int slot = 0;
                    for (final JsonElement it : e.getValue().getAsJsonArray())
                    {
                        final JsonArray a = it.getAsJsonArray();
                        final Item item = BuiltInRegistries.ITEM.get(ResourceLocation.parse(a.get(0).getAsString()));
                        int count = a.get(1).getAsInt();
                        while (count > 0 && slot < c.getContainerSize())
                        {
                            final int n = Math.min(count, item.getDefaultMaxStackSize());
                            c.setItem(slot++, new ItemStack(item, n));
                            count -= n;
                        }
                    }
                    c.setChanged();
                }
            }
            final JsonArray spawns = f.spec.getAsJsonArray("spawns");
            if (spawns != null)
            {
                for (final JsonElement it : spawns)
                {
                    final JsonArray a = it.getAsJsonArray();
                    final EntityType<?> type = EntityType.byString(a.get(0).getAsString()).orElse(null);
                    if (type == null)
                    {
                        f.error = "unknown entity " + a.get(0).getAsString();
                        continue;
                    }
                    final BlockPos p = f.anchor.offset(a.get(1).getAsInt(), a.get(2).getAsInt(), a.get(3).getAsInt());
                    for (int n = 0; n < a.get(4).getAsInt(); n++)
                    {
                        final Entity ent = type.spawn(level, p, MobSpawnType.COMMAND);
                        if (ent instanceof Mob m && m.getType().getCategory().isFriendly())
                        {
                            m.setPersistenceRequired();
                        }
                    }
                }
            }
        }
        level.getServer().tickRateManager().requestGameToSprint(maxTicks + 200);
        log("inputs loaded, mobs spawned, sprinting %d ticks", maxTicks);
    }

    private static BlockPos rel(final String key)
    {
        final String[] p = key.split(",");
        return new BlockPos(Integer.parseInt(p[0]), Integer.parseInt(p[1]), Integer.parseInt(p[2]));
    }

    /** Default random tick speed is 3 per 16x16x16 section; x10 for the test, applied to the blocks that tick. */
    private void randomTicks(final ServerLevel level)
    {
        for (final Farm f : farms)
        {
            if (!f.built || runTicks > f.ticks)
            {
                continue;
            }
            // growing blocks change (cane grows a block up, saplings become logs...): re-scan the box now and then
            if (runTicks % 100 == 1)
            {
                f.randomTicking.clear();
                for (int x = 0; x < f.sx; x++)
                {
                    for (int y = 0; y < f.sy + 4; y++)
                    {
                        for (int z = 0; z < f.sz; z++)
                        {
                            final BlockPos p = f.origin.offset(x, y, z);
                            if (level.getBlockState(p).isRandomlyTicking())
                            {
                                f.randomTicking.add(p);
                            }
                        }
                    }
                }
            }
            // each block gets on average 30/4096 random ticks per game tick
            for (final BlockPos p : f.randomTicking)
            {
                if (random.nextInt(4096) < 30)
                {
                    final BlockState st = level.getBlockState(p);
                    if (st.isRandomlyTicking())
                    {
                        st.randomTick(level, p, random);
                    }
                }
            }
        }
    }

    private boolean check(final ServerLevel level)
    {
        boolean all = true;
        int pass = 0;
        for (final Farm f : farms)
        {
            final Map<String, Integer> got = new HashMap<>();
            final Map<String, Integer> inBox = new HashMap<>();
            if (f.built)
            {
                final JsonArray outs = f.spec.getAsJsonArray("outputs");
                if (outs != null)
                {
                    for (final JsonElement o : outs)
                    {
                        if (level.getBlockEntity(f.anchor.offset(rel(o.getAsString()))) instanceof Container c)
                        {
                            count(c, got);
                        }
                    }
                }
                for (int x = 0; x < f.sx; x++)
                {
                    for (int y = 0; y < f.sy; y++)
                    {
                        for (int z = 0; z < f.sz; z++)
                        {
                            if (level.getBlockEntity(f.origin.offset(x, y, z)) instanceof Container c)
                            {
                                count(c, inBox);
                            }
                        }
                    }
                }
            }
            boolean ok = f.built && f.error == null;
            final StringBuilder sb = new StringBuilder();
            for (final Map.Entry<String, JsonElement> e : f.spec.getAsJsonObject("expect").entrySet())
            {
                final int need = e.getValue().getAsInt();
                final int have = got.getOrDefault(e.getKey(), 0);
                sb.append(e.getKey().replace("minecraft:", "")).append(' ').append(have).append('/').append(need).append(", ");
                ok &= have >= need;
            }
            final JsonArray outs = f.spec.getAsJsonArray("outputs");
            if (f.spec.getAsJsonObject("expect").size() > 0 && (outs == null || outs.isEmpty()))
            {
                ok = false;
                sb.append("no farm_output container tagged, ");
            }
            log("%s %s: %s%s; all containers: %s", ok ? "PASS" : "FAIL", f.rel, sb, f.error == null ? "" : " error: " + f.error, inBox);
            all &= ok;
            pass += ok ? 1 : 0;
        }
        log("%d of %d farms work", pass, farms.size());
        return all;
    }

    private static void count(final Container c, final Map<String, Integer> into)
    {
        for (int i = 0; i < c.getContainerSize(); i++)
        {
            final ItemStack s = c.getItem(i);
            if (!s.isEmpty())
            {
                into.merge(BuiltInRegistries.ITEM.getKey(s.getItem()).toString(), s.getCount(), Integer::sum);
            }
        }
    }

    private void finish(final ServerLevel level, final boolean pass)
    {
        stage = -1;
        NeoterraTrade.LOG.info(pass ? "FARMTEST PASS" : "FARMTEST FAIL");
        level.getServer().halt(false);
    }

    private static void log(final String fmt, final Object... args)
    {
        NeoterraTrade.LOG.info("[farmtest] " + String.format(fmt, args));
    }
}
