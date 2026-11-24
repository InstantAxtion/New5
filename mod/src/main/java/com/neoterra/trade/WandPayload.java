package com.neoterra.trade;

import io.netty.buffer.ByteBuf;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.network.handling.IPayloadContext;

/** Client → server: Builder's Wand menu – new settings, or undo (undo = true). */
public record WandPayload(int action, int mode, int size, boolean undo) implements CustomPacketPayload
{
    public static final Type<WandPayload> TYPE = new Type<>(NeoterraTrade.id("wand"));
    public static final StreamCodec<ByteBuf, WandPayload> CODEC = StreamCodec.composite(
        ByteBufCodecs.VAR_INT, WandPayload::action, ByteBufCodecs.VAR_INT, WandPayload::mode,
        ByteBufCodecs.VAR_INT, WandPayload::size, ByteBufCodecs.BOOL, WandPayload::undo, WandPayload::new);

    @Override
    public Type<? extends CustomPacketPayload> type()
    {
        return TYPE;
    }

    static void handle(final WandPayload p, final IPayloadContext ctx)
    {
        ctx.enqueueWork(() -> {
            if (p.undo())
            {
                ctx.player().displayClientMessage(Component.literal(BuildWand.undo(ctx.player())).withStyle(ChatFormatting.GOLD), false);
                return;
            }
            final ItemStack wand = BuilderWandItem.wand(ctx.player());
            if (!wand.isEmpty())
            {
                BuilderWandItem.setSettings(wand, new BuildWand.Settings(p.action(), p.mode(), p.size()));
            }
        });
    }
}
