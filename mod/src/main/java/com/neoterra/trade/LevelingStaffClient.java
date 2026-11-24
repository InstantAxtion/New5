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

    /** The staff's menu: Flatten, Undo last flatten, Clear selection, Take stored blocks. */
    static void openMenu(final ItemStack stack)
    {
        Minecraft.getInstance().setScreen(new StaffScreen(stack));
    }

    private static final class StaffScreen extends net.minecraft.client.gui.screens.Screen
    {
        private final ItemStack stack;

        StaffScreen(final ItemStack stack)
        {
            super(net.minecraft.network.chat.Component.literal("Leveling Staff"));
            this.stack = stack;
        }

        @Override
        protected void init()
        {
            final int w = 160, x = (width - w) / 2;
            int y = height / 2 - 30;
            final boolean full = LevelingStaffItem.corner(stack, "a").isPresent() && LevelingStaffItem.corner(stack, "b").isPresent();
            final var flatten = net.minecraft.client.gui.components.Button.builder(net.minecraft.network.chat.Component.literal("Flatten"),
                b -> send(LevelingStaffItem.ACTION_FLATTEN)).bounds(x, y, w, 20).build();
            flatten.active = full;
            addRenderableWidget(flatten);
            addRenderableWidget(net.minecraft.client.gui.components.Button.builder(net.minecraft.network.chat.Component.literal("Undo last flatten"),
                b -> send(LevelingStaffItem.ACTION_UNDO)).bounds(x, y + 24, w, 20).build());
            addRenderableWidget(net.minecraft.client.gui.components.Button.builder(net.minecraft.network.chat.Component.literal("Clear selection"),
                b -> send(LevelingStaffItem.ACTION_CLEAR)).bounds(x, y + 48, w, 20).build());
            final var take = net.minecraft.client.gui.components.Button.builder(net.minecraft.network.chat.Component.literal(
                "Take stored blocks (" + LevelingStaffItem.storeTotal(stack) + ")"), b -> send(LevelingStaffItem.ACTION_TAKE)).bounds(x, y + 72, w, 20).build();
            take.active = LevelingStaffItem.storeTotal(stack) > 0;
            addRenderableWidget(take);
        }

        private void send(final int action)
        {
            net.neoforged.neoforge.network.PacketDistributor.sendToServer(new StaffActionPayload(action));
            onClose();
        }

        @Override
        public void render(final net.minecraft.client.gui.GuiGraphics g, final int mx, final int my, final float pt)
        {
            super.render(g, mx, my, pt);
            final Optional<BlockPos> a = LevelingStaffItem.corner(stack, "a");
            final Optional<BlockPos> b = LevelingStaffItem.corner(stack, "b");
            final String info = a.isEmpty() ? "No selection – right-click a block for corner 1"
                : b.isEmpty() ? "Corner 1 set: ground level y " + a.get().getY() + " – right-click corner 2"
                : "Area " + (Math.abs(a.get().getX() - b.get().getX()) + 1) + " x " + (Math.abs(a.get().getZ() - b.get().getZ()) + 1)
                    + ", ground level y " + a.get().getY();
            g.drawCenteredString(font, title, width / 2, height / 2 - 62, 0xFFD24A);
            g.drawCenteredString(font, info, width / 2, height / 2 - 46, 0xFFFFFF);
        }

        @Override
        public boolean isPauseScreen()
        {
            return false;
        }
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
