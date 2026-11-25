package com.neoterra.trade;

import io.netty.buffer.ByteBuf;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.ResourceLocation;
import net.neoforged.neoforge.network.handling.IPayloadContext;

/** Client → server: a button of the Stored blocks screen (take / discard / auto-discard / discard all). */
public record StorePayload(int action, String item, int amount) implements CustomPacketPayload
{
    public static final Type<StorePayload> TYPE = new Type<>(NeoterraTrade.id("store"));
    public static final StreamCodec<ByteBuf, StorePayload> CODEC = StreamCodec.composite(
        ByteBufCodecs.VAR_INT, StorePayload::action, ByteBufCodecs.STRING_UTF8, StorePayload::item,
        ByteBufCodecs.VAR_INT, StorePayload::amount, StorePayload::new);

    @Override
    public Type<? extends CustomPacketPayload> type()
    {
        return TYPE;
    }

    static void handle(final StorePayload p, final IPayloadContext ctx)
    {
        ctx.enqueueWork(() -> LevelingStaffItem.storeAction(ctx.player(), p.action(),
            p.item().isEmpty() ? net.minecraft.world.item.Items.AIR : BuiltInRegistries.ITEM.get(ResourceLocation.parse(p.item())), p.amount()));
    }
}
