package com.neoterra.trade;

import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.neoforged.neoforge.network.handling.IPayloadContext;

/** Client → server: a button of the Leveling Staff's menu was pressed. */
public record StaffActionPayload(int action) implements CustomPacketPayload
{
    public static final Type<StaffActionPayload> TYPE = new Type<>(NeoterraTrade.id("staff_action"));
    public static final StreamCodec<ByteBuf, StaffActionPayload> CODEC =
        ByteBufCodecs.VAR_INT.map(StaffActionPayload::new, StaffActionPayload::action);

    @Override
    public Type<? extends CustomPacketPayload> type()
    {
        return TYPE;
    }

    static void handle(final StaffActionPayload payload, final IPayloadContext ctx)
    {
        ctx.enqueueWork(() -> LevelingStaffItem.act(ctx.player(), payload.action()));
    }
}
