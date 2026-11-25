package com.neoterra.trade;

import io.netty.buffer.ByteBuf;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.neoforged.neoforge.network.handling.IPayloadContext;

/** Client → server: the Builder's Wand was used on this (possibly far) block face. */
public record WandClickPayload(BlockPos pos, int face) implements CustomPacketPayload
{
    public static final Type<WandClickPayload> TYPE = new Type<>(NeoterraTrade.id("wand_click"));
    public static final StreamCodec<ByteBuf, WandClickPayload> CODEC = StreamCodec.composite(
        BlockPos.STREAM_CODEC, WandClickPayload::pos, ByteBufCodecs.VAR_INT, WandClickPayload::face, WandClickPayload::new);

    @Override
    public Type<? extends CustomPacketPayload> type()
    {
        return TYPE;
    }

    static void handle(final WandClickPayload p, final IPayloadContext ctx)
    {
        ctx.enqueueWork(() -> BuilderWandItem.clicked(ctx.player(), p.pos(), Direction.from3DDataValue(p.face())));
    }
}
