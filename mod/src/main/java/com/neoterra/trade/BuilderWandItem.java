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

    @Override
    public InteractionResult useOn(final UseOnContext ctx)
    {
        final Player player = ctx.getPlayer();
        if (player == null || ctx.getHand() != InteractionHand.MAIN_HAND)
        {
            return InteractionResult.PASS;
        }
        if (ctx.getLevel().isClientSide)
        {
            return InteractionResult.SUCCESS;
        }
        final BlockHitResult hit = new BlockHitResult(ctx.getClickLocation(), ctx.getClickedFace(), ctx.getClickedPos(), ctx.isInside());
        final String msg = BuildWand.apply((ServerLevel) ctx.getLevel(), player, hit, settings(ctx.getItemInHand()), ctx.getItemInHand());
        player.displayClientMessage(Component.literal(msg).withStyle(ChatFormatting.GOLD), true);
        return InteractionResult.CONSUME;
    }

    @Override
    public InteractionResultHolder<ItemStack> use(final Level level, final Player player, final InteractionHand hand)
    {
        final ItemStack stack = player.getItemInHand(hand);
        if (level.isClientSide)
        {
            LevelingStaffClient.openWandMenu(stack);
        }
        return InteractionResultHolder.sidedSuccess(stack, level.isClientSide);
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
        lines.add(Component.literal("Right-click the air: menu (action, mode, size, undo)").withStyle(ChatFormatting.GRAY));
    }
}
