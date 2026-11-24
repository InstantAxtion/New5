package com.neoterra.trade;

import com.minecolonies.api.blocks.AbstractBlockHut;
import com.minecolonies.api.colony.IColony;
import com.minecolonies.api.colony.IColonyManager;
import com.minecolonies.api.colony.permissions.Action;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.BiomeTags;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.Container;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.common.Tags;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Leveling Staff logic: flatten the area between two corners to the height of the first corner.
 * <ul>
 *   <li>above the ground level everything is removed (terrain, trees, plants, water) – the player gets the drops;</li>
 *   <li>holes below it are filled with natural ground: the biome's surface block on top, 3 blocks of subsoil, stone
 *       deeper – one fill item (dirt, stone, sand, gravel...) per block, taken first from what was removed, then from
 *       the player's inventory; if there is not enough, nothing changes;</li>
 *   <li>containers, colony huts and unbreakable blocks are never touched: the job is refused instead.</li>
 * </ul>
 * The work is planned in one go (so it can be refused cleanly) and then carried out a few columns per tick.
 */
public final class Flattening
{
    public static final int MAX_SIZE  = 64;   // blocks per side
    public static final int MAX_ABOVE = 64;   // how far up it clears
    public static final int MAX_DEPTH = 32;   // how deep it fills a hole
    private static final int COLUMNS_PER_TICK = 256;

    private static final Set<Item> FILL = Set.of(
        Items.DIRT, Items.COARSE_DIRT, Items.ROOTED_DIRT, Items.GRASS_BLOCK, Items.PODZOL, Items.MYCELIUM, Items.MUD,
        Items.COBBLESTONE, Items.STONE, Items.COBBLED_DEEPSLATE, Items.DEEPSLATE, Items.ANDESITE, Items.DIORITE,
        Items.GRANITE, Items.TUFF, Items.CALCITE, Items.SAND, Items.RED_SAND, Items.GRAVEL, Items.SANDSTONE,
        Items.RED_SANDSTONE, Items.CLAY, Items.NETHERRACK);

    private static final List<Job> JOBS = new ArrayList<>();

    private Flattening() {}

    /** What the flattening will do. */
    public static final class Plan
    {
        final ServerLevel level;
        final int x1, z1, x2, z2, ground;
        final List<BlockPos> remove = new ArrayList<>();
        final Map<BlockPos, BlockState> place = new LinkedHashMap<>();
        final List<ItemStack> drops = new ArrayList<>();
        int fillNeeded;
        String refusal;

        Plan(final ServerLevel level, final int x1, final int z1, final int x2, final int z2, final int ground)
        {
            this.level = level;
            this.x1 = x1;
            this.z1 = z1;
            this.x2 = x2;
            this.z2 = z2;
            this.ground = ground;
        }

        public int sizeX() { return x2 - x1 + 1; }
        public int sizeZ() { return z2 - z1 + 1; }
        public String refusal() { return refusal; }
        public int fillNeeded() { return fillNeeded; }
    }

    private static final class Job
    {
        final Plan plan;
        final List<Map.Entry<BlockPos, BlockState>> steps = new ArrayList<>();
        int next;

        Job(final Plan plan)
        {
            this.plan = plan;
            for (final BlockPos p : plan.remove)
            {
                steps.add(Map.entry(p, Blocks.AIR.defaultBlockState()));
            }
            steps.addAll(plan.place.entrySet());
        }
    }

    /** Work out what flattening the area a..b to the ground height of a would do (no changes made). */
    public static Plan plan(final ServerLevel level, final Player player, final BlockPos a, final BlockPos b)
    {
        final Plan plan = new Plan(level, Math.min(a.getX(), b.getX()), Math.min(a.getZ(), b.getZ()),
            Math.max(a.getX(), b.getX()), Math.max(a.getZ(), b.getZ()), a.getY());
        if (plan.sizeX() > MAX_SIZE || plan.sizeZ() > MAX_SIZE)
        {
            plan.refusal = "The area is " + plan.sizeX() + "x" + plan.sizeZ() + " – at most " + MAX_SIZE + "x" + MAX_SIZE + ".";
            return plan;
        }
        final String noRight = permission(level, player, plan);
        if (noRight != null)
        {
            plan.refusal = noRight;
            return plan;
        }
        final ItemStack tool = new ItemStack(Items.DIAMOND_PICKAXE);
        final int top = Math.min(level.getMaxBuildHeight() - 1, plan.ground + MAX_ABOVE);
        final int bottom = Math.max(level.getMinBuildHeight() + 1, plan.ground - MAX_DEPTH);
        final BlockPos.MutableBlockPos m = new BlockPos.MutableBlockPos();
        for (int x = plan.x1; x <= plan.x2; x++)
        {
            for (int z = plan.z1; z <= plan.z2; z++)
            {
                // 1. clear everything above the ground level (removed top-down so sand and gravel can't fall)
                boolean cut = false;
                final List<BlockPos> column = new ArrayList<>();
                for (int y = plan.ground + 1; y <= top; y++)
                {
                    m.set(x, y, z);
                    final BlockState st = level.getBlockState(m);
                    if (st.isAir())
                    {
                        continue;
                    }
                    final String why = protectedBlock(level, m, st);
                    if (why != null)
                    {
                        plan.refusal = why + " at " + m.getX() + " " + m.getY() + " " + m.getZ() + " is in the area – move it or pick a smaller area.";
                        return plan;
                    }
                    final BlockPos p = m.immutable();
                    plan.drops.addAll(Block.getDrops(st, level, p, level.getBlockEntity(p), player, tool));
                    column.add(p);
                    cut |= st.isSolid();
                }
                for (int i = column.size() - 1; i >= 0; i--)
                {
                    plan.remove.add(column.get(i));
                }
                // 2. fill holes below it until solid ground (placed bottom-up), and give exposed terrain a natural top
                final Holder<Biome> biome = level.getBiome(m.set(x, plan.ground, z));
                final List<Map.Entry<BlockPos, BlockState>> fill = new ArrayList<>();
                for (int y = plan.ground; y >= bottom; y--)
                {
                    m.set(x, y, z);
                    final BlockState st = level.getBlockState(m);
                    final int depth = plan.ground - y;
                    if (isGround(st))
                    {
                        if (depth == 0 && isTerrain(st) && !st.is(surface(biome).getBlock()))
                        {
                            fill.add(Map.entry(m.immutable(), surface(biome)));
                        }
                        else if (depth > 0 && depth <= 3 && cut && isTerrain(st) && !st.is(subsoil(biome).getBlock()))
                        {
                            fill.add(Map.entry(m.immutable(), subsoil(biome)));
                        }
                        if ((depth > 0 && !cut) || depth >= 3)
                        {
                            break;
                        }
                        continue;
                    }
                    final String why = protectedBlock(level, m, st);
                    if (why != null)
                    {
                        plan.refusal = why + " at " + m.getX() + " " + m.getY() + " " + m.getZ() + " is in the area – move it or pick a smaller area.";
                        return plan;
                    }
                    if (!st.isAir())
                    {
                        plan.drops.addAll(Block.getDrops(st, level, m.immutable(), level.getBlockEntity(m), player, tool));
                    }
                    fill.add(Map.entry(m.immutable(), depth == 0 ? surface(biome) : depth <= 3 ? subsoil(biome) : Blocks.STONE.defaultBlockState()));
                    plan.fillNeeded++;
                }
                for (int i = fill.size() - 1; i >= 0; i--)
                {
                    plan.place.put(fill.get(i).getKey(), fill.get(i).getValue());
                }
            }
        }
        // fill comes first from what is removed, then from the player's inventory
        final int fromDrops = Math.min(plan.fillNeeded, countFill(plan.drops));
        final int fromInventory = plan.fillNeeded - fromDrops;
        if (!player.isCreative() && fromInventory > countFill(player.getInventory()))
        {
            plan.refusal = "Filling the holes needs " + plan.fillNeeded + " blocks of dirt, stone, sand or gravel; the area gives "
                + fromDrops + " and you carry " + countFill(player.getInventory()) + ". Bring " + (fromInventory - countFill(player.getInventory())) + " more.";
        }
        return plan;
    }

    /** Carry out a plan: take the fill, queue the block changes, give the player what is left over. */
    public static void start(final Plan plan, final Player player)
    {
        int needFromDrops = Math.min(plan.fillNeeded, countFill(plan.drops));
        int needFromInventory = plan.fillNeeded - needFromDrops;
        // use the removed dirt/stone first
        for (final ItemStack s : plan.drops)
        {
            if (needFromDrops > 0 && FILL.contains(s.getItem()))
            {
                final int n = Math.min(needFromDrops, s.getCount());
                s.shrink(n);
                needFromDrops -= n;
            }
        }
        if (!player.isCreative())
        {
            final var inv = player.getInventory();
            for (int i = 0; i < inv.getContainerSize() && needFromInventory > 0; i++)
            {
                final ItemStack s = inv.getItem(i);
                if (!s.isEmpty() && FILL.contains(s.getItem()))
                {
                    final int n = Math.min(needFromInventory, s.getCount());
                    s.shrink(n);
                    needFromInventory -= n;
                }
            }
        }
        for (final ItemStack s : plan.drops)
        {
            if (!s.isEmpty() && !player.getInventory().add(s))
            {
                player.drop(s, false);
            }
        }
        JOBS.add(new Job(plan));
    }

    /** Server tick: a few columns' worth of block changes per tick. */
    public static void tick()
    {
        if (JOBS.isEmpty())
        {
            return;
        }
        final Job job = JOBS.get(0);
        final int perTick = COLUMNS_PER_TICK * 8;
        for (int i = 0; i < perTick && job.next < job.steps.size(); i++, job.next++)
        {
            final Map.Entry<BlockPos, BlockState> e = job.steps.get(job.next);
            job.plan.level.setBlock(e.getKey(), e.getValue(), Block.UPDATE_ALL);
        }
        if (job.next >= job.steps.size())
        {
            JOBS.remove(0);
        }
    }

    /** Finish every queued job now (self-test). */
    static void runAll()
    {
        while (!JOBS.isEmpty())
        {
            tick();
        }
    }

    // ------------------------------------------------------------------------------------------------ helpers

    private static String permission(final ServerLevel level, final Player player, final Plan plan)
    {
        if (level.getServer().isUnderSpawnProtection(level, new BlockPos(plan.x1, plan.ground, plan.z1), player)
            || level.getServer().isUnderSpawnProtection(level, new BlockPos(plan.x2, plan.ground, plan.z2), player))
        {
            return "This area is under spawn protection.";
        }
        for (final int x : new int[] {plan.x1, plan.x2, (plan.x1 + plan.x2) / 2})
        {
            for (final int z : new int[] {plan.z1, plan.z2, (plan.z1 + plan.z2) / 2})
            {
                final IColony colony = IColonyManager.getInstance().getColonyByPosFromWorld(level, new BlockPos(x, plan.ground, z));
                if (colony != null && !colony.getPermissions().hasPermission(player, Action.BREAK_BLOCKS))
                {
                    return "You may not break blocks in the colony " + colony.getName() + ".";
                }
            }
        }
        return null;
    }

    private static String protectedBlock(final ServerLevel level, final BlockPos pos, final BlockState st)
    {
        if (st.getBlock() instanceof AbstractBlockHut<?>)
        {
            return "A colony hut";
        }
        if (st.getDestroySpeed(level, pos) < 0)
        {
            return "An unbreakable block (" + st.getBlock().getName().getString() + ")";
        }
        if (level.getBlockEntity(pos) instanceof Container)
        {
            return "A container (" + st.getBlock().getName().getString() + ")";
        }
        return null;
    }

    private static boolean isGround(final BlockState st)
    {
        return st.isSolid() && st.getFluidState().isEmpty() && !st.is(BlockTags.LEAVES) && !st.is(BlockTags.LOGS);
    }

    private static boolean isTerrain(final BlockState st)
    {
        return st.is(BlockTags.DIRT) || st.is(BlockTags.BASE_STONE_OVERWORLD) || st.is(BlockTags.SAND)
            || st.is(Blocks.GRAVEL) || st.is(Blocks.SANDSTONE) || st.is(Blocks.RED_SANDSTONE) || st.is(Blocks.CLAY)
            || st.is(Blocks.SNOW_BLOCK);
    }

    private static BlockState surface(final Holder<Biome> b)
    {
        if (b.is(Tags.Biomes.IS_DESERT) || b.is(BiomeTags.IS_BEACH))
        {
            return Blocks.SAND.defaultBlockState();
        }
        if (b.is(BiomeTags.IS_BADLANDS))
        {
            return Blocks.RED_SAND.defaultBlockState();
        }
        if (b.is(Tags.Biomes.IS_MUSHROOM))
        {
            return Blocks.MYCELIUM.defaultBlockState();
        }
        return Blocks.GRASS_BLOCK.defaultBlockState();
    }

    private static BlockState subsoil(final Holder<Biome> b)
    {
        if (b.is(Tags.Biomes.IS_DESERT) || b.is(BiomeTags.IS_BEACH))
        {
            return Blocks.SANDSTONE.defaultBlockState();
        }
        if (b.is(BiomeTags.IS_BADLANDS))
        {
            return Blocks.RED_SANDSTONE.defaultBlockState();
        }
        return Blocks.DIRT.defaultBlockState();
    }

    private static int countFill(final List<ItemStack> stacks)
    {
        int n = 0;
        for (final ItemStack s : stacks)
        {
            n += FILL.contains(s.getItem()) ? s.getCount() : 0;
        }
        return n;
    }

    private static int countFill(final net.minecraft.world.entity.player.Inventory inv)
    {
        int n = 0;
        for (int i = 0; i < inv.getContainerSize(); i++)
        {
            final ItemStack s = inv.getItem(i);
            n += FILL.contains(s.getItem()) ? s.getCount() : 0;
        }
        return n;
    }
}
