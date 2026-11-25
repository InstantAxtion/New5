package com.neoterra.trade;

import net.minecraft.ChatFormatting;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;

import java.util.List;

/**
 * Builder's Wand: right-click a block to Place / Replace / Destroy / Use in the chosen mode (Direction, Row/Column,
 * Fill, Area) with the block or item in the off hand; right-click the air for the menu (action, mode, size, undo).
 */
public class BuilderWandItem extends Item
{
    public BuilderWandItem(final Properties props)
    {
        super(props);
    }

    public static BuildWand.Settings settings(final ItemStack stack)
    {
        final CustomData data = stack.get(DataComponents.CUSTOM_DATA);
        final CompoundTag t = data == null ? new CompoundTag() : data.copyTag();
        return new BuildWand.Settings(t.contains("action") ? t.getInt("action") : BuildWand.PLACE,
            t.contains("mode") ? t.getInt("mode") : BuildWand.AREA, t.contains("size") ? t.getInt("size") : 3);
    }

    static void setSettings(final ItemStack stack, final BuildWand.Settings s)
    {
        final CompoundTag t = new CompoundTag();
        t.putInt("action", Math.floorMod(s.action(), 4));
        t.putInt("mode", Math.floorMod(s.mode(), 4));
        t.putInt("size", Math.max(1, Math.min(BuildWand.MAX_SIZE, s.size())));
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(t));
    }

    public static net.minecraft.core.BlockPos fillCorner(final ItemStack stack)
    {
        final CustomData data = stack.get(DataComponents.CUSTOM_DATA);
        final CompoundTag t = data == null ? new CompoundTag() : data.copyTag();
        return t.contains("fill") ? net.minecraft.nbt.NbtUtils.readBlockPos(t, "fill").orElse(null) : null;
    }

    static void setFillCorner(final ItemStack stack, final net.minecraft.core.BlockPos pos)
    {
        final CustomData data = stack.get(DataComponents.CUSTOM_DATA);
        final CompoundTag t = data == null ? new CompoundTag() : data.copyTag();
        if (pos == null)
        {
            t.remove("fill");
        }
        else
        {
            t.put("fill", net.minecraft.nbt.NbtUtils.writeBlockPos(pos));
        }
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(t));
    }

    static ItemStack wand(final Player player)
    {
        for (final InteractionHand hand : InteractionHand.values())
        {
            if (player.getItemInHand(hand).getItem() instanceof BuilderWandItem)
            {
                return player.getItemInHand(hand);
            }
        }
        return ItemStack.EMPTY;
    }

    /** How far the wand reaches: it works on the block you look at, as far as your view goes (loaded chunks). */
    public static final double RANGE = 1028;

    @Override
    public InteractionResult useOn(final UseOnContext ctx)
    {
        // near or far, every click goes through use(): the client aims and sends the target to the server
        return InteractionResult.PASS;
    }

    @Override
    public InteractionResultHolder<ItemStack> use(final Level level, final Player player, final InteractionHand hand)
    {
        final ItemStack stack = player.getItemInHand(hand);
        if (hand != InteractionHand.MAIN_HAND)
        {
            return InteractionResultHolder.pass(stack);
        }
        if (level.isClientSide)
        {
            if (player.isShiftKeyDown())
            {
                LevelingStaffClient.openWandMenu(stack);
            }
            else
            {
                LevelingStaffClient.wandClick(player);
            }
        }
        return InteractionResultHolder.sidedSuccess(stack, level.isClientSide);
    }

    /** Server: a click on a (possibly far) block, sent by the client. */
    static void clicked(final Player player, final net.minecraft.core.BlockPos pos, final net.minecraft.core.Direction face)
    {
        final ItemStack wand = wand(player);
        if (wand.isEmpty() || !(player.level() instanceof ServerLevel level))
        {
            return;
        }
        if (player.getEyePosition().distanceTo(net.minecraft.world.phys.Vec3.atCenterOf(pos)) > RANGE + 2 || !level.isLoaded(pos))
        {
            player.displayClientMessage(Component.literal("Out of range.").withStyle(ChatFormatting.RED), true);
            return;
        }
        final BlockHitResult hit = new BlockHitResult(net.minecraft.world.phys.Vec3.atCenterOf(pos).relative(face, 0.5), face, pos, false);
        final String msg = BuildWand.apply(level, player, hit, settings(wand), wand);
        player.displayClientMessage(Component.literal(msg).withStyle(ChatFormatting.GOLD), true);
    }

    @Override
    public void appendHoverText(final ItemStack stack, final TooltipContext ctx, final List<Component> lines, final TooltipFlag flag)
    {
        final BuildWand.Settings s = settings(stack);
        lines.add(Component.literal(BuildWand.ACTIONS[s.action()] + " · " + BuildWand.MODES[s.mode()]
            + (s.mode() == BuildWand.FILL ? " (corner to corner)" : " · size " + s.size())).withStyle(ChatFormatting.GOLD));
        final net.minecraft.core.BlockPos fc = fillCorner(stack);
        if (fc != null)
        {
            lines.add(Component.literal("Fill corner 1: " + fc.getX() + " " + fc.getY() + " " + fc.getZ()).withStyle(ChatFormatting.AQUA));
        }
        lines.add(Component.literal("Block or item to use: in your off hand").withStyle(ChatFormatting.GRAY));
        lines.add(Component.literal("Blocks come from your inventory first, the off hand last").withStyle(ChatFormatting.GRAY));
        lines.add(Component.literal("Right-click: works on the block you look at, up to " + (int) RANGE + " blocks away").withStyle(ChatFormatting.GRAY));
        lines.add(Component.literal("Sneak + right-click: menu (action, mode, size, undo)").withStyle(ChatFormatting.GRAY));
        final int stored = LevelingStaffItem.storeTotal(stack);
        if (stored > 0)
        {
            lines.add(Component.literal(stored + " blocks stored – Take them in the menu").withStyle(ChatFormatting.AQUA));
        }
    }
}
