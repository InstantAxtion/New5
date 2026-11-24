package com.neoterra.trade;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.NbtUtils;
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

import java.util.List;
import java.util.Optional;

/**
 * Leveling Staff: right-click a block = first corner (its height becomes the ground level), right-click another
 * block = opposite corner; sneak + right-click = flatten the area (see {@link Flattening}). Sneak + right-click
 * without a full selection clears it. The selection is stored on the staff, so the client can draw a preview box.
 */
public class LevelingStaffItem extends Item
{
    public LevelingStaffItem(final Properties props)
    {
        super(props);
    }

    public static Optional<BlockPos> corner(final ItemStack stack, final String key)
    {
        final CustomData data = stack.get(DataComponents.CUSTOM_DATA);
        if (data == null)
        {
            return Optional.empty();
        }
        final CompoundTag tag = data.copyTag();
        return tag.contains(key) ? NbtUtils.readBlockPos(tag, key) : Optional.empty();
    }

    private static void setCorners(final ItemStack stack, final BlockPos a, final BlockPos b)
    {
        final CompoundTag tag = new CompoundTag();
        if (a != null)
        {
            tag.put("a", NbtUtils.writeBlockPos(a));
        }
        if (b != null)
        {
            tag.put("b", NbtUtils.writeBlockPos(b));
        }
        if (tag.isEmpty())
        {
            stack.remove(DataComponents.CUSTOM_DATA);
        }
        else
        {
            stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        }
    }

    @Override
    public InteractionResult useOn(final UseOnContext ctx)
    {
        final Player player = ctx.getPlayer();
        if (player == null)
        {
            return InteractionResult.PASS;
        }
        if (ctx.getLevel().isClientSide)
        {
            return InteractionResult.SUCCESS;
        }
        final ItemStack stack = ctx.getItemInHand();
        if (player.isShiftKeyDown())
        {
            flatten((ServerLevel) ctx.getLevel(), player, stack);
            return InteractionResult.CONSUME;
        }
        final BlockPos pos = ctx.getClickedPos();
        final Optional<BlockPos> a = corner(stack, "a");
        final Optional<BlockPos> b = corner(stack, "b");
        if (a.isEmpty() || b.isPresent())
        {
            setCorners(stack, pos, null);
            say(player, "Corner 1 set – the ground will be level with this block (y " + pos.getY() + "). Now right-click the opposite corner.");
        }
        else
        {
            setCorners(stack, a.get(), pos);
            final int sx = Math.abs(pos.getX() - a.get().getX()) + 1;
            final int sz = Math.abs(pos.getZ() - a.get().getZ()) + 1;
            say(player, "Area " + sx + " x " + sz + " at ground level y " + a.get().getY() + ". Sneak + right-click to flatten it.");
        }
        return InteractionResult.CONSUME;
    }

    @Override
    public InteractionResultHolder<ItemStack> use(final Level level, final Player player, final InteractionHand hand)
    {
        final ItemStack stack = player.getItemInHand(hand);
        if (!player.isShiftKeyDown())
        {
            return InteractionResultHolder.pass(stack);
        }
        if (!level.isClientSide)
        {
            flatten((ServerLevel) level, player, stack);
        }
        return InteractionResultHolder.sidedSuccess(stack, level.isClientSide);
    }

    private static void flatten(final ServerLevel level, final Player player, final ItemStack stack)
    {
        final Optional<BlockPos> a = corner(stack, "a");
        final Optional<BlockPos> b = corner(stack, "b");
        if (a.isEmpty() || b.isEmpty())
        {
            setCorners(stack, null, null);
            say(player, "Selection cleared. Right-click two corners first.");
            return;
        }
        final Flattening.Plan plan = Flattening.plan(level, player, a.get(), b.get());
        if (plan.refusal() != null)
        {
            player.sendSystemMessage(Component.literal(plan.refusal()).withStyle(ChatFormatting.RED));
            return;
        }
        Flattening.start(plan, player);
        setCorners(stack, null, null);
        say(player, "Flattening " + plan.sizeX() + " x " + plan.sizeZ() + " to y " + a.get().getY()
            + (plan.fillNeeded() > 0 ? " (" + plan.fillNeeded() + " blocks of fill used)" : "") + ". Removed blocks are in your inventory.");
    }

    private static void say(final Player player, final String text)
    {
        player.displayClientMessage(Component.literal(text).withStyle(ChatFormatting.GOLD), false);
    }

    @Override
    public void appendHoverText(final ItemStack stack, final TooltipContext ctx, final List<Component> lines, final TooltipFlag flag)
    {
        lines.add(Component.literal("Right-click two corners, sneak + right-click to flatten").withStyle(ChatFormatting.GRAY));
        lines.add(Component.literal("Ground level = the first corner's height").withStyle(ChatFormatting.GRAY));
        lines.add(Component.literal("Max " + Flattening.MAX_SIZE + " x " + Flattening.MAX_SIZE + "; fills holes with your dirt/stone").withStyle(ChatFormatting.DARK_GRAY));
        corner(stack, "a").ifPresent(p -> lines.add(Component.literal("Corner 1: " + p.getX() + " " + p.getY() + " " + p.getZ()).withStyle(ChatFormatting.GOLD)));
        corner(stack, "b").ifPresent(p -> lines.add(Component.literal("Corner 2: " + p.getX() + " " + p.getY() + " " + p.getZ()).withStyle(ChatFormatting.GOLD)));
    }
}
