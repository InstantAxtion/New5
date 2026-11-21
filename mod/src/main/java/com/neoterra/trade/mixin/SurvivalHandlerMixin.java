package com.neoterra.trade.mixin;

import com.ldtteam.structurize.api.RotationMirror;
import com.ldtteam.structurize.blueprints.v1.Blueprint;
import com.minecolonies.api.blocks.AbstractBlockHut;
import com.minecolonies.core.placementhandlers.main.SurvivalHandler;
import com.neoterra.trade.NeoterraConfig;
import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * Build tool placement (server): when the player has no hut block of the building, lend one for this placement.
 * MineColonies' handler consumes it on success; if the placement is refused (outside the colony, no permission...)
 * the loaned block is taken back again, so no free hut blocks are created.
 */
@Mixin(value = SurvivalHandler.class, remap = false)
public abstract class SurvivalHandlerMixin
{
    private static final ThreadLocal<Block> NEOTERRA_LOAN = new ThreadLocal<>();

    @Inject(method = "handle", at = @At("HEAD"))
    private void neoterra$lendHut(final Blueprint blueprint, final String packName, final String blueprintPath, final boolean clientPack,
                                  final Level world, final Player player, final BlockPos pos, final RotationMirror rotationMirror,
                                  final CallbackInfo ci)
    {
        NEOTERRA_LOAN.remove();
        if (!NeoterraConfig.freeHuts() || player == null || player.isCreative() || blueprint == null)
        {
            return;
        }
        final Block anchor = blueprint.getBlockState(blueprint.getPrimaryBlockOffset()).getBlock();
        if (anchor instanceof AbstractBlockHut<?> && count(player, anchor) == 0 && player.getInventory().add(new ItemStack(anchor)))
        {
            NEOTERRA_LOAN.set(anchor);
        }
    }

    @Inject(method = "handle", at = @At("RETURN"))
    private void neoterra$returnLoan(final Blueprint blueprint, final String packName, final String blueprintPath, final boolean clientPack,
                                     final Level world, final Player player, final BlockPos pos, final RotationMirror rotationMirror,
                                     final CallbackInfo ci)
    {
        final Block loan = NEOTERRA_LOAN.get();
        NEOTERRA_LOAN.remove();
        if (loan == null)
        {
            return;
        }
        // placement refused: the loaned block is still there - take it back
        final var inv = player.getInventory();
        for (int i = 0; i < inv.getContainerSize(); i++)
        {
            final ItemStack s = inv.getItem(i);
            if (!s.isEmpty() && s.is(loan.asItem()))
            {
                s.shrink(1);
                break;
            }
        }
    }

    private static int count(final Player player, final Block block)
    {
        int n = 0;
        final var inv = player.getInventory();
        for (int i = 0; i < inv.getContainerSize(); i++)
        {
            final ItemStack s = inv.getItem(i);
            if (!s.isEmpty() && s.is(block.asItem()))
            {
                n += s.getCount();
            }
        }
        return n;
    }
}
