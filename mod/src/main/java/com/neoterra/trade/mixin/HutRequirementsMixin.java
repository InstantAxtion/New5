package com.neoterra.trade.mixin;

import com.minecolonies.api.blocks.AbstractBlockHut;
import com.neoterra.trade.NeoterraConfig;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.network.chat.contents.TranslatableContents;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import java.util.List;

/** Build tool (client): a hut's blueprints are listed and placeable without the hut block in the inventory. */
@Mixin(value = AbstractBlockHut.class, remap = false)
public abstract class HutRequirementsMixin
{
    @Inject(method = "getRequirements", at = @At("RETURN"))
    private void neoterra$noHutItemNeeded(final ClientLevel level, final BlockPos pos, final LocalPlayer player,
                                          final CallbackInfoReturnable<List<MutableComponent>> cir)
    {
        if (!NeoterraConfig.freeHuts() || cir.getReturnValue() == null)
        {
            return;
        }
        cir.getReturnValue().removeIf(c -> c.getContents() instanceof TranslatableContents t
            && t.getKey().startsWith("com.minecolonies.coremod.hut.cost"));
    }
}
