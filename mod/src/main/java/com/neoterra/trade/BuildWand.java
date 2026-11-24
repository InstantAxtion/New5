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
    public static final int MAX_SIZE = 32;      // line length; area side is capped at 16
    public static final int MAX_BLOCKS = 256;   // per click

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

    /** The blocks one click would affect (in order). Pure geometry + a few block checks; safe on the client. */
    public static final int MAX_FILL = 4096;    // corner-to-corner fill, at most 32 per side

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
                final int side = Math.min(16, n);
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
                if (Math.abs(from.getX() - base.getX()) < 32 && Math.abs(from.getY() - base.getY()) < 32 && Math.abs(from.getZ() - base.getZ()) < 32)
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
            if (list.size() >= (s.mode() == FILL ? MAX_FILL : MAX_BLOCKS) || !level.isInWorldBounds(p))
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
            if (Math.abs(corner.getX() - c2.getX()) >= 32 || Math.abs(corner.getY() - c2.getY()) >= 32 || Math.abs(corner.getZ() - c2.getZ()) >= 32)
            {
                return "Fill is at most 32 blocks on each side – pick a closer corner.";
            }
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
        final Undo undo = new Undo();
        undo.level = level;
        int done = 0, skipped = 0;
        final ItemStack tool = new ItemStack(Items.DIAMOND_PICKAXE);
        for (final BlockPos p : targets)
        {
            if (!mayChange(level, player, p))
            {
                skipped++;
                continue;
            }
            final BlockState old = level.getBlockState(p);
            final BlockEntity oldBe = level.getBlockEntity(p);
            if ((s.action() == REPLACE || s.action() == DESTROY) && protectedBlock(level, p, old))
            {
                skipped++;
                continue;
            }
            final CompoundTag oldTag = oldBe == null ? null : oldBe.saveWithFullMetadata(level.registryAccess());
            switch (s.action())
            {
                case PLACE, REPLACE ->
                {
                    final BlockItem bi = (BlockItem) off.getItem();
                    if (s.action() == REPLACE && old.is(bi.getBlock()))
                    {
                        continue;
                    }
                    BlockState st = bi.getBlock().getStateForPlacement(new BlockPlaceContext(player, InteractionHand.OFF_HAND, off,
                        new BlockHitResult(Vec3.atCenterOf(p), hit.getDirection(), p, false)));
                    if (st == null)
                    {
                        st = bi.getBlock().defaultBlockState();
                    }
                    if (!st.canSurvive(level, p))
                    {
                        skipped++;
                        continue;
                    }
                    if (!player.isCreative() && !takeOne(player, bi, undo.taken))
                    {
                        finish(player, undo);
                        return done + " blocks done – out of " + bi.getDescription().getString() + ".";
                    }
                    if (s.action() == REPLACE && !player.isCreative())
                    {
                        giveAll(player, Block.getDrops(old, level, p, oldBe, player, tool), undo.given);
                    }
                    undo.before.add(new Old(p, old, oldTag));
                    level.setBlock(p, st, Block.UPDATE_ALL);
                    done++;
                }
                case DESTROY ->
                {
                    if (!player.isCreative())
                    {
                        giveAll(player, Block.getDrops(old, level, p, oldBe, player, tool), undo.given);
                    }
                    undo.before.add(new Old(p, old, oldTag));
                    level.setBlock(p, net.minecraft.world.level.block.Blocks.AIR.defaultBlockState(), Block.UPDATE_ALL);
                    done++;
                }
                default ->
                {
                    if (off.isEmpty())
                    {
                        finish(player, undo);
                        return done + " blocks done – your off-hand item is used up.";
                    }
                    final int countBefore = off.getCount();
                    final var result = off.getItem().useOn(new UseOnContext(level, player, InteractionHand.OFF_HAND, off,
                        new BlockHitResult(Vec3.atCenterOf(p).relative(hit.getDirection(), 0.5), hit.getDirection(), p, false)));
                    if (result.consumesAction())
                    {
                        undo.before.add(new Old(p, old, oldTag));
                        if (off.getCount() < countBefore)
                        {
                            undo.taken.merge(off.getItem(), countBefore - off.getCount(), Integer::sum);
                        }
                        done++;
                    }
                }
            }
        }
        finish(player, undo);
        return done + " block" + (done == 1 ? "" : "s") + " " + switch (s.action())
        {
            case PLACE -> "placed";
            case REPLACE -> "replaced";
            case DESTROY -> "removed";
            default -> "used";
        } + (skipped > 0 ? " (" + skipped + " skipped: protected or can't go there)" : "") + ".";
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
                final int have = player.getInventory().countItem(e.getKey());
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
                remove(player.getInventory(), e.getKey(), e.getValue());
            }
            for (final Map.Entry<Item, Integer> e : undo.taken.entrySet())
            {
                giveAll(player, List.of(new ItemStack(e.getKey(), e.getValue())), null);
            }
        }
        for (int i = undo.before.size() - 1; i >= 0; i--)
        {
            final Old o = undo.before.get(i);
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
            final ItemStack c = s.copy();
            if (!player.getInventory().add(c) && !c.isEmpty())
            {
                player.drop(c, false);
            }
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
