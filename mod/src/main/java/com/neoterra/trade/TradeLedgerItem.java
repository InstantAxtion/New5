package com.neoterra.trade;

import com.minecolonies.api.colony.IColony;
import com.minecolonies.api.colony.IColonyManager;
import com.minecolonies.api.colony.buildings.IBuilding;
import com.minecolonies.api.colony.permissions.Action;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.NbtUtils;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;

import java.util.List;

/**
 * Trade Ledger. Right-click a Trade Post to remember it, then right-click a Trade Post of another
 * colony to link the two. Sneak + right-click a post to switch it between Import &amp; Export,
 * Export only and Import only. Sneak + right-click a post that is linked to nothing clears the ledger.
 */
public class TradeLedgerItem extends Item
{
    private static final String[] MODES = {"import & export", "export only", "import only"};

    public TradeLedgerItem(final Properties properties)
    {
        super(properties);
    }

    @Override
    public InteractionResult onItemUseFirst(final ItemStack stack, final UseOnContext ctx)
    {
        final Level level = ctx.getLevel();
        final Player player = ctx.getPlayer();
        if (player == null || !(level.getBlockState(ctx.getClickedPos()).getBlock() instanceof BlockHutTradePost))
        {
            return InteractionResult.PASS;
        }
        if (level.isClientSide)
        {
            return InteractionResult.SUCCESS;
        }
        final BlockPos pos = ctx.getClickedPos();
        final IColony colony = IColonyManager.getInstance().getColonyByPosFromWorld(level, pos);
        final IBuilding b = colony == null ? null : colony.getServerBuildingManager().getBuilding(pos);
        if (!(b instanceof BuildingTradePost post))
        {
            say(player, "This Trade Post is not part of a colony yet.", ChatFormatting.RED);
            return InteractionResult.FAIL;
        }
        if (!colony.getPermissions().hasPermission(player, Action.MANAGE_HUTS))
        {
            say(player, "You are not allowed to manage huts in " + colony.getName() + ".", ChatFormatting.RED);
            return InteractionResult.FAIL;
        }

        if (player.isShiftKeyDown())
        {
            if (!post.isLinked())
            {
                stack.remove(DataComponents.CUSTOM_DATA);
                say(player, "Ledger cleared.", ChatFormatting.GRAY);
            }
            else
            {
                say(player, "Trade Post set to " + MODES[post.cycleMode()] + ".", ChatFormatting.GOLD);
            }
            return InteractionResult.SUCCESS;
        }

        final CompoundTag saved = stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag();
        if (!saved.contains("colony"))
        {
            final CompoundTag t = new CompoundTag();
            t.putInt("colony", colony.getID());
            t.putString("dim", colony.getDimension().location().toString());
            t.put("pos", NbtUtils.writeBlockPos(pos));
            t.putString("name", colony.getName());
            CustomData.set(DataComponents.CUSTOM_DATA, stack, t);
            say(player, "Trade Post of " + colony.getName() + " written in the ledger. Now use it on a Trade Post of another colony.", ChatFormatting.GREEN);
            return InteractionResult.SUCCESS;
        }

        final IColony first = IColonyManager.getInstance().getColonyByDimension(saved.getInt("colony"), BuildingTradePost.dim(saved.getString("dim")));
        final BlockPos firstPos = NbtUtils.readBlockPos(saved, "pos").orElse(BlockPos.ZERO);
        stack.remove(DataComponents.CUSTOM_DATA);
        if (first == null || !(first.getServerBuildingManager().getBuilding(firstPos) instanceof BuildingTradePost firstPost))
        {
            say(player, "The Trade Post in the ledger no longer exists. Ledger cleared.", ChatFormatting.RED);
            return InteractionResult.FAIL;
        }
        if (first.getID() == colony.getID() && first.getDimension().equals(colony.getDimension()))
        {
            say(player, "Both Trade Posts are in the same colony – pick a post in another colony. Ledger cleared.", ChatFormatting.RED);
            return InteractionResult.FAIL;
        }
        if (!first.getPermissions().hasPermission(player, Action.MANAGE_HUTS))
        {
            say(player, "You are not allowed to manage huts in " + first.getName() + ".", ChatFormatting.RED);
            return InteractionResult.FAIL;
        }
        unlinkOld(firstPost);
        unlinkOld(post);
        firstPost.link(colony, pos);
        post.link(first, firstPos);
        say(player, "Linked " + first.getName() + " ⇄ " + colony.getName() + ". Hire a Trade Courier at each post that should export.", ChatFormatting.GREEN);
        return InteractionResult.SUCCESS;
    }

    /** A post can only have one partner: drop the previous link on both ends. */
    private static void unlinkOld(final BuildingTradePost post)
    {
        final BuildingTradePost old = post.getPartner();
        if (old != null)
        {
            old.unlink();
        }
        post.unlink();
    }

    private static void say(final Player player, final String text, final ChatFormatting colour)
    {
        player.displayClientMessage(Component.literal(text).withStyle(colour), false);
    }

    @Override
    public void appendHoverText(final ItemStack stack, final TooltipContext context, final List<Component> tooltip, final TooltipFlag flag)
    {
        final CompoundTag saved = stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag();
        if (saved.contains("colony"))
        {
            tooltip.add(Component.literal("Holds the Trade Post of " + saved.getString("name")).withStyle(ChatFormatting.GOLD));
        }
        tooltip.add(Component.literal("Use on two Trade Posts in different colonies to link them").withStyle(ChatFormatting.GRAY));
        tooltip.add(Component.literal("Sneak-use on a post: import / export mode").withStyle(ChatFormatting.GRAY));
    }

    @Override
    public boolean isFoil(final ItemStack stack)
    {
        return stack.has(DataComponents.CUSTOM_DATA);
    }
}
