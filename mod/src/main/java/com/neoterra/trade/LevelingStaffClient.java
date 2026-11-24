package com.neoterra.trade;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.LevelRenderer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.core.BlockPos;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.client.event.RenderLevelStageEvent;
import net.neoforged.neoforge.common.NeoForge;

import java.util.Optional;

/** Client only: draws the Leveling Staff's selection – the new ground level as a box over the area. */
final class LevelingStaffClient
{
    private LevelingStaffClient() {}

    static void register()
    {
        NeoForge.EVENT_BUS.addListener(LevelingStaffClient::onRender);
    }

    private static void onRender(final RenderLevelStageEvent event)
    {
        if (event.getStage() != RenderLevelStageEvent.Stage.AFTER_TRANSLUCENT_BLOCKS)
        {
            return;
        }
        final Minecraft mc = Minecraft.getInstance();
        if (mc.player == null)
        {
            return;
        }
        ItemStack stack = mc.player.getMainHandItem();
        if (!(stack.getItem() instanceof LevelingStaffItem))
        {
            stack = mc.player.getOffhandItem();
            if (!(stack.getItem() instanceof LevelingStaffItem))
            {
                return;
            }
        }
        final Optional<BlockPos> a = LevelingStaffItem.corner(stack, "a");
        if (a.isEmpty())
        {
            return;
        }
        final BlockPos b = LevelingStaffItem.corner(stack, "b").orElse(a.get());
        final int y = a.get().getY();
        final AABB ground = new AABB(Math.min(a.get().getX(), b.getX()), y + 1, Math.min(a.get().getZ(), b.getZ()),
            Math.max(a.get().getX(), b.getX()) + 1, y + 1.02, Math.max(a.get().getZ(), b.getZ()) + 1);
        final AABB above = ground.setMaxY(y + 4);
        final Vec3 cam = event.getCamera().getPosition();
        final PoseStack pose = event.getPoseStack();
        pose.pushPose();
        pose.translate(-cam.x, -cam.y, -cam.z);
        final MultiBufferSource.BufferSource buffers = mc.renderBuffers().bufferSource();
        final VertexConsumer lines = buffers.getBuffer(RenderType.lines());
        LevelRenderer.renderLineBox(pose, lines, above, 1.0f, 0.75f, 0.2f, 0.5f);
        LevelRenderer.renderLineBox(pose, lines, ground, 1.0f, 0.85f, 0.1f, 1.0f);
        LevelRenderer.renderLineBox(pose, lines, new AABB(a.get()).inflate(0.01), 0.2f, 1.0f, 0.3f, 1.0f);
        buffers.endBatch(RenderType.lines());
        pose.popPose();
    }
}
