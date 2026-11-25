package com.neoterra.trade;

import com.minecolonies.api.blocks.AbstractBlockHut;
import com.minecolonies.api.colony.IColony;
import com.minecolonies.api.colony.IColonyManager;
import com.minecolonies.api.colony.permissions.Action;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Container;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * Builder's Wand logic, shared by server (doing it) and client (the outline preview).
 * Actions: PLACE / REPLACE / DESTROY / USE. Modes: DIRECTION / ROW_COLUMN / FILL / AREA. Size 1..MAX_SIZE.
 * The block to place (or item to use) is the one in the off hand; placed blocks come from the inventory first and
 * the off-hand stack last. The last operation of each player can be undone.
 */
public final class BuildWand
{
    public static final int PLACE = 0, REPLACE = 1, DESTROY = 2, USE = 3;
    public static final int DIRECTION = 0, ROW_COLUMN = 1, FILL = 2, AREA = 3;
    public static final String[] ACTIONS = {"Place", "Replace", "Destroy", "Use"};
    public static final String[] MODES = {"Direction", "Row/Column", "Fill", "Area"};
    public static final int MAX_SIZE = 1028;          // line length, area side and fill side
    public static final int MAX_BLOCKS = 1_100_000;  // per click
    private static final int SYNC_LIMIT = 4096;       // bigger jobs run over several ticks
    private static final int BLOCKS_PER_TICK = 4096;

    private static final Map<UUID, Undo> UNDO = new HashMap<>();

    private BuildWand() {}

    public record Settings(int action, int mode, int size) {}

    private record Old(BlockPos pos, BlockState state, CompoundTag blockEntity) {}

    private static final class Undo
    {
        Level level;
        final List<Old> before = new ArrayList<>();
        final Map<Item, Integer> given = new LinkedHashMap<>();
        final Map<Item, Integer> taken = new LinkedHashMap<>();
    }

    // ================================================================================================ targets


    /** The cell a click points at: the space in front of the face when placing, else the clicked block. */
    public static BlockPos cell(final BlockHitResult hit, final Settings s)
    {
        return s.action() == PLACE ? hit.getBlockPos().relative(hit.getDirection()) : hit.getBlockPos();
    }

    public static List<BlockPos> targets(final Level level, final Player player, final BlockHitResult hit, final Settings s)
    {
        return targets(level, player, hit, s, null);
    }

    /** fillCorner: the first corner of a corner-to-corner fill (FILL mode), or null before it is set. */
    public static List<BlockPos> targets(final Level level, final Player player, final BlockHitResult hit, final Settings s, final BlockPos fillCorner)
    {
        final BlockPos clicked = hit.getBlockPos();
        final Direction face = hit.getDirection();
        final boolean place = s.action() == PLACE;
        final BlockPos base = place ? clicked.relative(face) : clicked;
        final int n = Math.max(1, Math.min(MAX_SIZE, s.size()));
        final Set<BlockPos> out = new LinkedHashSet<>();
        switch (s.mode())
        {
            case DIRECTION ->
            {
                // straight out of the face when building, into it when replacing / destroying / using
                final Direction d = place ? face : face.getOpposite();
                for (int i = 0; i < n; i++)
                {
                    out.add(base.relative(d, i));
                }
            }
            case ROW_COLUMN ->
            {
                final Direction d = inPlane(player.getLookAngle(), face);
                final int half = (n - 1) / 2;
                for (int i = -half; i < n - half; i++)
                {
                    out.add(base.relative(d, i));
                }
            }
            case AREA ->
            {
                final int side = n;
                final Direction[] ax = planeAxes(face);
                final int half = (side - 1) / 2;
                for (int i = -half; i < side - half; i++)
                {
                    for (int j = -half; j < side - half; j++)
                    {
                        out.add(base.relative(ax[0], i).relative(ax[1], j));
                    }
                }
            }
            default ->
            {
                // FILL: the box from the first corner to this one (just this cell before the first corner is set)
                final BlockPos from = fillCorner == null ? base : fillCorner;
                if (Math.abs(from.getX() - base.getX()) < MAX_SIZE && Math.abs(from.getY() - base.getY()) < MAX_SIZE
                    && Math.abs(from.getZ() - base.getZ()) < MAX_SIZE
                    && (long) (Math.abs(from.getX() - base.getX()) + 1) * (Math.abs(from.getY() - base.getY()) + 1) * (Math.abs(from.getZ() - base.getZ()) + 1) <= MAX_BLOCKS)
                {
                    for (final BlockPos q : BlockPos.betweenClosed(from, base))
                    {
                        out.add(q.immutable());
                    }
                }
            }
        }
        // keep only cells the action can work on
        final List<BlockPos> list = new ArrayList<>();
        for (final BlockPos p : out)
        {
            if (list.size() >= MAX_BLOCKS || !level.isInWorldBounds(p) || !level.isLoaded(p))
            {
                continue;
            }
            final BlockState st = level.getBlockState(p);
            final boolean ok = switch (s.action())
            {
                case PLACE -> st.canBeReplaced();
                case REPLACE, DESTROY -> !st.isAir() && st.getFluidState().isEmpty();
                default -> !st.isAir();
            };
            if (ok)
            {
                list.add(p);
            }
        }
        return list;
    }

    /** The box a click covers, without looking at blocks (cheap; for the preview of big jobs). */
    public static BlockPos[] bounds(final Player player, final BlockHitResult hit, final Settings s, final BlockPos fillCorner)
    {
        final Direction face = hit.getDirection();
        final boolean place = s.action() == PLACE;
        final BlockPos base = place ? hit.getBlockPos().relative(face) : hit.getBlockPos();
        final int n = Math.max(1, Math.min(MAX_SIZE, s.size()));
        final int half = (n - 1) / 2;
        return switch (s.mode())
        {
            case DIRECTION -> new BlockPos[] {base, base.relative(place ? face : face.getOpposite(), n - 1)};
            case ROW_COLUMN ->
            {
                final Direction d = inPlane(player.getLookAngle(), face);
                yield new BlockPos[] {base.relative(d, -half), base.relative(d, n - 1 - half)};
            }
            case AREA ->
            {
                final Direction[] ax = planeAxes(face);
                yield new BlockPos[] {base.relative(ax[0], -half).relative(ax[1], -half), base.relative(ax[0], n - 1 - half).relative(ax[1], n - 1 - half)};
            }
            default -> new BlockPos[] {fillCorner == null ? base : fillCorner, base};
        };
    }

    public static long volume(final BlockPos[] b)
    {
        return (long) (Math.abs(b[0].getX() - b[1].getX()) + 1) * (Math.abs(b[0].getY() - b[1].getY()) + 1) * (Math.abs(b[0].getZ() - b[1].getZ()) + 1);
    }

    private static Direction[] planeAxes(final Direction face)
    {
        return switch (face.getAxis())
        {
            case Y -> new Direction[] {Direction.EAST, Direction.SOUTH};
            case X -> new Direction[] {Direction.SOUTH, Direction.UP};
            default -> new Direction[] {Direction.EAST, Direction.UP};
        };
    }

    /** The in-plane direction the player looks along most (row on a floor, row or column on a wall). */
    private static Direction inPlane(final Vec3 look, final Direction face)
    {
        final Direction[] ax = planeAxes(face);
        final double a = Math.abs(look.x * ax[0].getStepX() + look.y * ax[0].getStepY() + look.z * ax[0].getStepZ());
        final double b = Math.abs(look.x * ax[1].getStepX() + look.y * ax[1].getStepY() + look.z * ax[1].getStepZ());
        return a >= b ? ax[0] : ax[1];
    }

    // ================================================================================================ doing it

    /** Carry out one click. Returns a message for the player. */
    public static String apply(final ServerLevel level, final Player player, final BlockHitResult hit, final Settings s)
    {
        return apply(level, player, hit, s, null);
    }

    /** wand: the wand stack, which remembers the first corner of a FILL (may be null: then FILL acts on one cell). */
    public static String apply(final ServerLevel level, final Player player, final BlockHitResult hit, final Settings s, final net.minecraft.world.item.ItemStack wand)
    {
        BlockPos corner = null;
        if (s.mode() == FILL && wand != null)
        {
            corner = BuilderWandItem.fillCorner(wand);
            if (corner == null)
            {
                BuilderWandItem.setFillCorner(wand, cell(hit, s));
                final BlockPos c = cell(hit, s);
                return "Fill: first corner " + c.getX() + " " + c.getY() + " " + c.getZ() + " – now click the opposite corner.";
            }
            final BlockPos c2 = cell(hit, s);
            BuilderWandItem.setFillCorner(wand, null);
            if (Math.abs(corner.getX() - c2.getX()) >= MAX_SIZE || Math.abs(corner.getY() - c2.getY()) >= MAX_SIZE || Math.abs(corner.getZ() - c2.getZ()) >= MAX_SIZE)
            {
                return "Fill is at most " + MAX_SIZE + " blocks on each side – pick a closer corner.";
            }
            if (volume(new BlockPos[] {corner, c2}) > MAX_BLOCKS)
            {
                return "That box has " + volume(new BlockPos[] {corner, c2}) + " blocks – at most " + MAX_BLOCKS + " at a time.";
            }
        }
        if (JOBS.stream().anyMatch(j -> j.player == player))
        {
            return "The wand is still working on your last job – wait a moment.";
        }
        final List<BlockPos> targets = targets(level, player, hit, s, corner);
        if (targets.isEmpty())
        {
            return "Nothing to do here.";
        }
        final ItemStack off = player.getOffhandItem();
        if ((s.action() == PLACE || s.action() == REPLACE) && !(off.getItem() instanceof BlockItem))
        {
            return "Hold the block to " + (s.action() == PLACE ? "place" : "replace with") + " in your off hand.";
        }
        if (s.action() == USE && off.isEmpty())
        {
            return "Hold the item to use (bone meal, a hoe, a shovel, an axe...) in your off hand.";
        }
        if ((s.action() == PLACE || s.action() == REPLACE) && !player.isCreative())
        {
            final BlockItem bi = (BlockItem) off.getItem();
            int need = 0;
            for (final BlockPos p : targets)
            {
                need += s.action() == REPLACE && level.getBlockState(p).is(bi.getBlock()) ? 0 : 1;
            }
            final int have = countBlock(player, bi);
            if (need > have)
            {
                return "That needs " + need + " " + bi.getDescription().getString() + "; you carry " + have + ". Bring " + (need - have) + " more.";
            }
        }
        final Job job = new Job(level, player, s, hit.getDirection(), targets);
        if (targets.size() <= SYNC_LIMIT)
        {
            run(job, Integer.MAX_VALUE);
            return job.message();
        }
        JOBS.add(job);
        return "Working on " + targets.size() + " blocks – this takes a few seconds.";
    }

    /** One click's work; big ones are done a few thousand blocks per tick. */
    private static final class Job
    {
        final ServerLevel level;
        final Player player;
        final Settings s;
        final Direction face;
        final List<BlockPos> targets;
        final Undo undo = new Undo();
        int next, done, skipped;
        String stop;
        BlockItem blockItem;

        BlockItem blockItem()
        {
            return blockItem;
        }

        Job(final ServerLevel level, final Player player, final Settings s, final Direction face, final List<BlockPos> targets)
        {
            this.level = level;
            this.player = player;
            this.s = s;
            this.face = face;
            this.targets = targets;
            undo.level = level;
            if (player.getOffhandItem().getItem() instanceof BlockItem bi)
            {
                blockItem = bi;
            }
        }

        String message()
        {
            return done + " block" + (done == 1 ? "" : "s") + " " + switch (s.action())
            {
                case PLACE -> "placed";
                case REPLACE -> "replaced";
                case DESTROY -> "removed";
                default -> "used";
            } + (skipped > 0 ? " (" + skipped + " skipped: protected or can't go there)" : "") + (stop != null ? " – " + stop : "") + ".";
        }
    }

    private static final List<Job> JOBS = new ArrayList<>();
    private static final List<Runnable> RESTORES = new ArrayList<>();

    /** Server tick: continue big jobs. */
    public static void tick()
    {
        if (!JOBS.isEmpty())
        {
            final Job job = JOBS.get(0);
            if (run(job, BLOCKS_PER_TICK))
            {
                JOBS.remove(0);
                job.player.displayClientMessage(net.minecraft.network.chat.Component.literal(job.message())
                    .withStyle(net.minecraft.ChatFormatting.GOLD), false);
            }
        }
        for (int i = 0; i < BLOCKS_PER_TICK && !RESTORES.isEmpty(); i++)
        {
            RESTORES.remove(RESTORES.size() - 1).run();
        }
    }

    /** Finish all queued work now (self-test). */
    static void runAll()
    {
        while (!JOBS.isEmpty() || !RESTORES.isEmpty())
        {
            tick();
        }
    }

    /** Works up to `limit` blocks of the job; true when finished. */
    private static boolean run(final Job job, final int limit)
    {
        final ItemStack tool = new ItemStack(Items.DIAMOND_PICKAXE);
        final ServerLevel level = job.level;
        final Player player = job.player;
        final ItemStack off = player.getOffhandItem();
        for (int k = 0; k < limit && job.next < job.targets.size() && job.stop == null; k++)
        {
            final BlockPos p = job.targets.get(job.next++);
            if (!mayChange(level, player, p))
            {
                job.skipped++;
                continue;
            }
            final BlockState old = level.getBlockState(p);
            final BlockEntity oldBe = level.getBlockEntity(p);
            if ((job.s.action() == REPLACE || job.s.action() == DESTROY) && protectedBlock(level, p, old))
            {
                job.skipped++;
                continue;
            }
            final CompoundTag oldTag = oldBe == null ? null : oldBe.saveWithFullMetadata(level.registryAccess());
            switch (job.s.action())
            {
                case PLACE, REPLACE ->
                {
                    final BlockItem bi = job.blockItem();
                    if (job.s.action() == REPLACE && old.is(bi.getBlock()))
                    {
                        continue;
                    }
                    BlockState st = bi.getBlock().getStateForPlacement(new BlockPlaceContext(player, InteractionHand.OFF_HAND,
                        new ItemStack(bi), new BlockHitResult(Vec3.atCenterOf(p), job.face, p, false)));
                    if (st == null)
                    {
                        st = bi.getBlock().defaultBlockState();
                    }
                    if (!st.canSurvive(level, p))
                    {
                        job.skipped++;
                        continue;
                    }
                    if (!player.isCreative() && !takeOne(player, bi, job.undo.taken))
                    {
                        job.stop = "out of " + bi.getDescription().getString();
                        break;
                    }
                    if (job.s.action() == REPLACE && !player.isCreative())
                    {
                        giveAll(player, Block.getDrops(old, level, p, oldBe, player, tool), job.undo.given);
                    }
                    job.undo.before.add(new Old(p, old, oldTag));
                    level.setBlock(p, st, Block.UPDATE_ALL);
                    job.done++;
                }
                case DESTROY ->
                {
                    if (!player.isCreative())
                    {
                        giveAll(player, Block.getDrops(old, level, p, oldBe, player, tool), job.undo.given);
                    }
                    job.undo.before.add(new Old(p, old, oldTag));
                    level.setBlock(p, net.minecraft.world.level.block.Blocks.AIR.defaultBlockState(), Block.UPDATE_ALL);
                    job.done++;
                }
                default ->
                {
                    if (off.isEmpty())
                    {
                        job.stop = "your off-hand item is used up";
                        break;
                    }
                    final int countBefore = off.getCount();
                    final var result = off.getItem().useOn(new UseOnContext(level, player, InteractionHand.OFF_HAND, off,
                        new BlockHitResult(Vec3.atCenterOf(p).relative(job.face, 0.5), job.face, p, false)));
                    if (result.consumesAction())
                    {
                        job.undo.before.add(new Old(p, old, oldTag));
                        if (off.getCount() < countBefore)
                        {
                            job.undo.taken.merge(off.getItem(), countBefore - off.getCount(), Integer::sum);
                        }
                        job.done++;
                    }
                }
            }
        }
        final boolean finished = job.next >= job.targets.size() || job.stop != null;
        if (finished)
        {
            finish(player, job.undo);
        }
        return finished;
    }

    private static void finish(final Player player, final Undo undo)
    {
        if (!undo.before.isEmpty())
        {
            UNDO.put(player.getUUID(), undo);
        }
    }

    /** Undo the player's last wand click. Returns a message. */
    public static String undo(final Player player)
    {
        final Undo undo = UNDO.get(player.getUUID());
        if (undo == null)
        {
            return "There is nothing to undo.";
        }
        if (undo.level != player.level())
        {
            return "Go back to the dimension of your last wand use to undo it.";
        }
        if (!player.isCreative())
        {
            final StringBuilder missing = new StringBuilder();
            for (final Map.Entry<Item, Integer> e : undo.given.entrySet())
            {
                final int have = player.getInventory().countItem(e.getKey()) + LevelingStaffItem.store(player).getOrDefault(e.getKey(), 0);
                if (have < e.getValue())
                {
                    missing.append(e.getValue() - have).append(' ').append(e.getKey().getDescription().getString()).append(", ");
                }
            }
            if (!missing.isEmpty())
            {
                return "To undo, give back what the wand gave you. Missing: " + missing.substring(0, missing.length() - 2) + ".";
            }
            for (final Map.Entry<Item, Integer> e : undo.given.entrySet())
            {
                final int fromStore = LevelingStaffItem.storeTake(player, e.getKey(), e.getValue());
                remove(player.getInventory(), e.getKey(), e.getValue() - fromStore);
            }
            for (final Map.Entry<Item, Integer> e : undo.taken.entrySet())
            {
                giveAll(player, List.of(new ItemStack(e.getKey(), e.getValue())), null);
            }
        }
        // restore in reverse order; RESTORES is worked from its end, so add oldest first
        final List<Runnable> work = new ArrayList<>();
        for (final Old o : undo.before)
        {
            work.add(() -> {
                undo.level.setBlock(o.pos(), o.state(), Block.UPDATE_ALL);
                if (o.blockEntity() != null)
                {
                    final BlockEntity be = undo.level.getBlockEntity(o.pos());
                    if (be != null)
                    {
                        be.loadWithComponents(o.blockEntity(), undo.level.registryAccess());
                        be.setChanged();
                    }
                }
            });
        }
        if (work.size() <= SYNC_LIMIT)
        {
            for (int i = work.size() - 1; i >= 0; i--)
            {
                work.get(i).run();
            }
        }
        else
        {
            RESTORES.addAll(work);
        }
        UNDO.remove(player.getUUID());
        return "Undone: " + undo.before.size() + " blocks put back.";
    }

    // ================================================================================================ items

    /** One block from the inventory first (not the off hand), the off-hand stack last. */
    private static boolean takeOne(final Player player, final BlockItem item, final Map<Item, Integer> taken)
    {
        final Inventory inv = player.getInventory();
        for (int i = 0; i < inv.items.size(); i++)
        {
            final ItemStack st = inv.items.get(i);
            if (st.is(item) && st.getComponentsPatch().isEmpty())
            {
                st.shrink(1);
                taken.merge(item, 1, Integer::sum);
                return true;
            }
        }
        final ItemStack off = player.getOffhandItem();
        if (off.is(item) && !off.isEmpty())
        {
            off.shrink(1);
            taken.merge(item, 1, Integer::sum);
            return true;
        }
        return false;
    }

    /** Blocks of this kind the player carries (inventory + off hand). */
    private static int countBlock(final Player player, final BlockItem item)
    {
        return player.getInventory().countItem(item);
    }

    /** Gives items: inventory first, the rest into the wand's (or staff's) store – never a flood of dropped items. */
    private static void giveAll(final Player player, final List<ItemStack> stacks, final Map<Item, Integer> record)
    {
        for (final ItemStack s : stacks)
        {
            if (s.isEmpty())
            {
                continue;
            }
            if (record != null)
            {
                record.merge(s.getItem(), s.getCount(), Integer::sum);
            }
            Flattening.give(player, s.getItem(), s.getCount());
        }
    }

    private static void remove(final Inventory inv, final Item item, int count)
    {
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

    // ================================================================================================ rules

    private static boolean mayChange(final ServerLevel level, final Player player, final BlockPos p)
    {
        if (level.getServer().isUnderSpawnProtection(level, p, player) || !level.mayInteract(player, p))
        {
            return false;
        }
        final IColony colony = IColonyManager.getInstance().getColonyByPosFromWorld(level, p);
        return colony == null || colony.getPermissions().hasPermission(player, Action.BREAK_BLOCKS);
    }

    private static boolean protectedBlock(final ServerLevel level, final BlockPos p, final BlockState st)
    {
        return st.getBlock() instanceof AbstractBlockHut<?> || st.getDestroySpeed(level, p) < 0
            || level.getBlockEntity(p) instanceof Container;
    }
}
