package com.neoterra.trade;

import com.minecolonies.api.blocks.AbstractBlockHut;
import com.minecolonies.api.colony.IColony;
import com.minecolonies.api.colony.IColonyManager;
import com.minecolonies.api.colony.permissions.Action;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.BiomeTags;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.Container;
import net.minecraft.world.entity.player.Inventory;
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
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * Leveling Staff logic: flatten the area between two corners to the height of the FIRST corner (the second corner's
 * height never matters).
 * <ul>
 *   <li>above the ground level everything is removed (terrain, trees, plants, water) – the player gets the drops,
 *       into the inventory and, when that is full, into the staff's store;</li>
 *   <li>holes below it are filled with natural ground: the biome's surface block on top, 3 blocks of subsoil, stone
 *       deeper – one fill item (dirt, stone, sand, gravel...) per block, taken first from what was removed, then from
 *       the player's inventory and the staff's store; if there is not enough, nothing changes;</li>
 *   <li>containers, colony huts and unbreakable blocks are never touched: the job is refused instead;</li>
 *   <li>the last flatten of each player can be undone: every block (with its block-entity data) comes back, the
 *       drops are taken back and the fill is returned.</li>
 * </ul>
 * The work is planned in one go (so it can be refused cleanly) and then carried out a few thousand blocks per tick.
 */
public final class Flattening
{
    public static final int MAX_SIZE  = 192;  // blocks per side
    public static final int MAX_ABOVE = 64;   // how far up it clears
    public static final int MAX_DEPTH = 32;   // how deep it fills a hole
    private static final int BLOCKS_PER_TICK = 4096;

    private static final Set<Item> FILL = Set.of(
        Items.DIRT, Items.COARSE_DIRT, Items.ROOTED_DIRT, Items.GRASS_BLOCK, Items.PODZOL, Items.MYCELIUM, Items.MUD,
        Items.COBBLESTONE, Items.STONE, Items.COBBLED_DEEPSLATE, Items.DEEPSLATE, Items.ANDESITE, Items.DIORITE,
        Items.GRANITE, Items.TUFF, Items.CALCITE, Items.SAND, Items.RED_SAND, Items.GRAVEL, Items.SANDSTONE,
        Items.RED_SANDSTONE, Items.CLAY, Items.NETHERRACK);

    private static final List<Job> JOBS = new ArrayList<>();
    private static final Map<UUID, Undo> UNDO = new HashMap<>();

    private Flattening() {}

    /** What the flattening will do. */
    public static final class Plan
    {
        final ServerLevel level;
        final int x1, z1, x2, z2, ground;
        final List<BlockPos> remove = new ArrayList<>();
        final Map<BlockPos, BlockState> place = new LinkedHashMap<>();
        final Map<Item, Integer> drops = new LinkedHashMap<>();
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
        public int ground() { return ground; }
    }

    private record Step(BlockPos pos, BlockState state, CompoundTag blockEntity) {}

    /** What one player's last flatten changed, to put it back. */
    private static final class Undo
    {
        final ServerLevel level;
        final List<Step> before = new ArrayList<>();      // old state of every changed block, in change order
        final Map<Item, Integer> given = new LinkedHashMap<>();   // drops the player received
        final Map<Item, Integer> taken = new LinkedHashMap<>();   // fill taken from the player
        boolean complete;

        Undo(final ServerLevel level) { this.level = level; }
    }

    private static final class Job
    {
        final ServerLevel level;
        final List<Step> steps;
        final Undo record;     // filled while the job runs (null for an undo job)
        int next;

        Job(final ServerLevel level, final List<Step> steps, final Undo record)
        {
            this.level = level;
            this.steps = steps;
            this.record = record;
        }
    }

    // ================================================================================================ planning

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
        if (busy(level))
        {
            plan.refusal = "The staff is still working on the last job – wait a moment.";
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
                    addAll(plan.drops, Block.getDrops(st, level, p, level.getBlockEntity(p), player, tool));
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
                        addAll(plan.drops, Block.getDrops(st, level, m.immutable(), level.getBlockEntity(m), player, tool));
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
        // fill comes first from what is removed, then from the player's inventory and the staff's store
        final int fromDrops = Math.min(plan.fillNeeded, countFill(plan.drops));
        final int fromPlayer = plan.fillNeeded - fromDrops;
        final int carried = countFill(player.getInventory()) + countFill(LevelingStaffItem.store(player));
        if (!player.isCreative() && fromPlayer > carried)
        {
            plan.refusal = "Filling the holes needs " + plan.fillNeeded + " blocks of dirt, stone, sand or gravel; the area gives "
                + fromDrops + " and you carry " + carried + ". Bring " + (fromPlayer - carried) + " more.";
        }
        return plan;
    }

    // ================================================================================================ running

    /** Carry out a plan: take the fill, queue the block changes, give the player what is left over. */
    public static void start(final Plan plan, final Player player)
    {
        final Undo undo = new Undo(plan.level);
        int needFromDrops = Math.min(plan.fillNeeded, countFill(plan.drops));
        int needFromPlayer = plan.fillNeeded - needFromDrops;
        // use the removed dirt/stone first
        for (final Map.Entry<Item, Integer> e : plan.drops.entrySet())
        {
            if (needFromDrops > 0 && FILL.contains(e.getKey()))
            {
                final int n = Math.min(needFromDrops, e.getValue());
                e.setValue(e.getValue() - n);
                needFromDrops -= n;
            }
        }
        if (!player.isCreative() && needFromPlayer > 0)
        {
            needFromPlayer = takeFill(player, needFromPlayer, undo.taken);
        }
        // what is left goes to the player: inventory first, then the staff's store
        for (final Map.Entry<Item, Integer> e : plan.drops.entrySet())
        {
            if (e.getValue() > 0 && !LevelingStaffItem.isVoided(player, e.getKey()))
            {
                give(player, e.getKey(), e.getValue());
                undo.given.merge(e.getKey(), e.getValue(), Integer::sum);
            }
        }
        final List<Step> steps = new ArrayList<>();
        for (final BlockPos p : plan.remove)
        {
            steps.add(new Step(p, Blocks.AIR.defaultBlockState(), null));
        }
        for (final Map.Entry<BlockPos, BlockState> e : plan.place.entrySet())
        {
            steps.add(new Step(e.getKey(), e.getValue(), null));
        }
        UNDO.put(player.getUUID(), undo);
        JOBS.add(new Job(plan.level, steps, undo));
    }

    /** Undo the player's last flatten. Returns null when started, else why not. */
    public static String undo(final Player player)
    {
        final Undo undo = UNDO.get(player.getUUID());
        if (undo == null)
        {
            return "There is nothing to undo.";
        }
        if (!undo.complete || busy(undo.level))
        {
            return "The staff is still working – undo when it has finished.";
        }
        if (undo.level != player.level())
        {
            return "Go back to the dimension of your last flatten to undo it.";
        }
        if (!player.isCreative())
        {
            // the blocks that come back must be handed back first (no duplicating)
            final StringBuilder missing = new StringBuilder();
            for (final Map.Entry<Item, Integer> e : undo.given.entrySet())
            {
                final int have = count(player, e.getKey());
                if (have < e.getValue())
                {
                    missing.append(e.getValue() - have).append(' ').append(e.getKey().getDescription().getString()).append(", ");
                }
            }
            if (!missing.isEmpty())
            {
                return "To undo, you must give back what the flatten gave you. Missing: " + missing.substring(0, missing.length() - 2) + ".";
            }
            for (final Map.Entry<Item, Integer> e : undo.given.entrySet())
            {
                take(player, e.getKey(), e.getValue());
            }
            for (final Map.Entry<Item, Integer> e : undo.taken.entrySet())
            {
                give(player, e.getKey(), e.getValue());
            }
        }
        final List<Step> steps = new ArrayList<>();
        for (int i = undo.before.size() - 1; i >= 0; i--)
        {
            steps.add(undo.before.get(i));
        }
        UNDO.remove(player.getUUID());
        JOBS.add(new Job(undo.level, steps, null));
        return null;
    }

    public static boolean canUndo(final Player player)
    {
        return UNDO.containsKey(player.getUUID());
    }

    /** Server tick: a few thousand block changes per tick. */
    public static void tick()
    {
        if (JOBS.isEmpty())
        {
            return;
        }
        final Job job = JOBS.get(0);
        for (int i = 0; i < BLOCKS_PER_TICK && job.next < job.steps.size(); i++, job.next++)
        {
            final Step s = job.steps.get(job.next);
            if (job.record != null)
            {
                final BlockEntity old = job.level.getBlockEntity(s.pos());
                job.record.before.add(new Step(s.pos(), job.level.getBlockState(s.pos()),
                    old == null ? null : old.saveWithFullMetadata(job.level.registryAccess())));
            }
            job.level.setBlock(s.pos(), s.state(), Block.UPDATE_ALL);
            if (s.blockEntity() != null)
            {
                final BlockEntity be = job.level.getBlockEntity(s.pos());
                if (be != null)
                {
                    be.loadWithComponents(s.blockEntity(), job.level.registryAccess());
                    be.setChanged();
                }
            }
        }
        if (job.next >= job.steps.size())
        {
            if (job.record != null)
            {
                job.record.complete = true;
            }
            JOBS.remove(0);
        }
    }

    private static boolean busy(final ServerLevel level)
    {
        return !JOBS.isEmpty();
    }

    /** Finish every queued job now (self-test). */
    static void runAll()
    {
        while (!JOBS.isEmpty())
        {
            tick();
        }
    }

    // ================================================================================================ items

    private static void addAll(final Map<Item, Integer> into, final List<ItemStack> stacks)
    {
        for (final ItemStack s : stacks)
        {
            if (!s.isEmpty())
            {
                into.merge(s.getItem(), s.getCount(), Integer::sum);
            }
        }
    }

    /** Give items: inventory first, the rest into the staff's store (never dropped on the ground while a staff is carried). */
    static void give(final Player player, final Item item, int count)
    {
        final int max = item.getDefaultMaxStackSize();
        while (count > 0)
        {
            final ItemStack s = new ItemStack(item, Math.min(count, max));
            final int n = s.getCount();
            player.getInventory().add(s);
            count -= n - s.getCount();
            if (!s.isEmpty())
            {
                LevelingStaffItem.storeAdd(player, item, count);
                return;
            }
        }
    }

    /** Give items to the inventory only; what does not fit goes back into the staff's store. */
    static void giveInventoryOnly(final Player player, final Item item, int count)
    {
        final int max = item.getDefaultMaxStackSize();
        while (count > 0)
        {
            final ItemStack s = new ItemStack(item, Math.min(count, max));
            final int n = s.getCount();
            player.getInventory().add(s);
            count -= n - s.getCount();
            if (!s.isEmpty())
            {
                LevelingStaffItem.storeAdd(player, item, count);
                return;
            }
        }
    }

    /** No staff to store into: drop the rest at the player's feet in full stacks. */
    static void dropAt(final Player player, final Item item, int count)
    {
        while (count > 0)
        {
            final int n = Math.min(count, item.getDefaultMaxStackSize());
            player.drop(new ItemStack(item, n), false);
            count -= n;
        }
    }

    private static int count(final Player player, final Item item)
    {
        return player.getInventory().countItem(item) + LevelingStaffItem.store(player).getOrDefault(item, 0);
    }

    /** Take items: from the staff's store first, then the inventory. */
    private static void take(final Player player, final Item item, int count)
    {
        count -= LevelingStaffItem.storeTake(player, item, count);
        final Inventory inv = player.getInventory();
        for (int i = 0; i < inv.getContainerSize() && count > 0; i++)
        {
            final ItemStack s = inv.getItem(i);
            if (s.is(item))
            {
                final int n = Math.min(count, s.getCount());
                s.shrink(n);
                count -= n;
            }
        }
    }

    /** Take `count` fill items of any kind (store first, then inventory); records what was taken. Returns the shortfall. */
    private static int takeFill(final Player player, int count, final Map<Item, Integer> taken)
    {
        for (final Map.Entry<Item, Integer> e : new ArrayList<>(LevelingStaffItem.store(player).entrySet()))
        {
            if (count > 0 && FILL.contains(e.getKey()))
            {
                final int n = LevelingStaffItem.storeTake(player, e.getKey(), Math.min(count, e.getValue()));
                taken.merge(e.getKey(), n, Integer::sum);
                count -= n;
            }
        }
        final Inventory inv = player.getInventory();
        for (int i = 0; i < inv.getContainerSize() && count > 0; i++)
        {
            final ItemStack s = inv.getItem(i);
            if (!s.isEmpty() && FILL.contains(s.getItem()))
            {
                final int n = Math.min(count, s.getCount());
                taken.merge(s.getItem(), n, Integer::sum);
                s.shrink(n);
                count -= n;
            }
        }
        return count;
    }

    private static int countFill(final Map<Item, Integer> items)
    {
        int n = 0;
        for (final Map.Entry<Item, Integer> e : items.entrySet())
        {
            n += FILL.contains(e.getKey()) ? e.getValue() : 0;
        }
        return n;
    }

    private static int countFill(final Inventory inv)
    {
        int n = 0;
        for (int i = 0; i < inv.getContainerSize(); i++)
        {
            final ItemStack s = inv.getItem(i);
            n += FILL.contains(s.getItem()) ? s.getCount() : 0;
        }
        return n;
    }

    // ================================================================================================ rules

    private static String permission(final ServerLevel level, final Player player, final Plan plan)
    {
        if (level.getServer().isUnderSpawnProtection(level, new BlockPos(plan.x1, plan.ground, plan.z1), player)
            || level.getServer().isUnderSpawnProtection(level, new BlockPos(plan.x2, plan.ground, plan.z2), player))
        {
            return "This area is under spawn protection.";
        }
        for (int x = plan.x1; x <= plan.x2 + 15; x += 16)
        {
            for (int z = plan.z1; z <= plan.z2 + 15; z += 16)
            {
                final BlockPos p = new BlockPos(Math.min(x, plan.x2), plan.ground, Math.min(z, plan.z2));
                final IColony colony = IColonyManager.getInstance().getColonyByPosFromWorld(level, p);
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

    // ================================================================================================ store codec

    static Map<Item, Integer> readStore(final CompoundTag tag)
    {
        final Map<Item, Integer> out = new LinkedHashMap<>();
        if (tag != null && tag.contains("store", Tag.TAG_LIST))
        {
            final ListTag list = tag.getList("store", Tag.TAG_COMPOUND);
            for (int i = 0; i < list.size(); i++)
            {
                final CompoundTag e = list.getCompound(i);
                final Item item = BuiltInRegistries.ITEM.get(ResourceLocation.parse(e.getString("id")));
                if (item != Items.AIR && e.getInt("n") > 0)
                {
                    out.merge(item, e.getInt("n"), Integer::sum);
                }
            }
        }
        return out;
    }

    static void writeStore(final CompoundTag tag, final Map<Item, Integer> store)
    {
        final ListTag list = new ListTag();
        for (final Map.Entry<Item, Integer> e : store.entrySet())
        {
            if (e.getValue() > 0)
            {
                final CompoundTag c = new CompoundTag();
                c.putString("id", BuiltInRegistries.ITEM.getKey(e.getKey()).toString());
                c.putInt("n", e.getValue());
                list.add(c);
            }
        }
        if (list.isEmpty())
        {
            tag.remove("store");
        }
        else
        {
            tag.put("store", list);
        }
    }
}
