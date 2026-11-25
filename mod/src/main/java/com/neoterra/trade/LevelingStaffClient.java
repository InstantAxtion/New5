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

    static void register(final net.neoforged.bus.api.IEventBus modBus)
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

    // ------------------------------------------------------------------------------------------------ Builder's Wand

    /** Aim as far as the wand reaches and send the target to the server. */
    static void wandClick(final net.minecraft.world.entity.player.Player player)
    {
        final net.minecraft.world.phys.HitResult hit = player.pick(BuilderWandItem.RANGE, 1.0f, false);
        if (hit instanceof net.minecraft.world.phys.BlockHitResult bh && hit.getType() == net.minecraft.world.phys.HitResult.Type.BLOCK)
        {
            net.neoforged.neoforge.network.PacketDistributor.sendToServer(new WandClickPayload(bh.getBlockPos(), bh.getDirection().get3DDataValue()));
        }
        else
        {
            player.displayClientMessage(net.minecraft.network.chat.Component.literal("No block in sight (sneak + right-click for the menu)."), true);
        }
    }

    static void openWandMenu(final ItemStack stack)
    {
        Minecraft.getInstance().setScreen(new WandScreen(stack));
    }

    /** Two lists like a classic building gadget: Action (Place/Replace/Destroy/Use) and Mode, plus size and undo. */
    private static final class WandScreen extends net.minecraft.client.gui.screens.Screen
    {
        private final ItemStack stack;
        private int action, mode, size;

        WandScreen(final ItemStack stack)
        {
            super(net.minecraft.network.chat.Component.literal("Builder's Wand"));
            this.stack = stack;
            final BuildWand.Settings s = BuilderWandItem.settings(stack);
            action = s.action();
            mode = s.mode();
            size = s.size();
        }

        private int left() { return width / 2 - 110; }
        private int top() { return height / 2 - 60; }

        @Override
        protected void init()
        {
            final int y = top() + 108;
            addRenderableWidget(net.minecraft.client.gui.components.Button.builder(net.minecraft.network.chat.Component.literal("-10"),
                b -> setSize(size - 10)).bounds(left(), y, 22, 20).build());
            addRenderableWidget(net.minecraft.client.gui.components.Button.builder(net.minecraft.network.chat.Component.literal("-1"),
                b -> setSize(size - 1)).bounds(left() + 23, y, 18, 20).build());
            addRenderableWidget(net.minecraft.client.gui.components.Button.builder(net.minecraft.network.chat.Component.literal("+1"),
                b -> setSize(size + 1)).bounds(left() + 59, y, 18, 20).build());
            addRenderableWidget(net.minecraft.client.gui.components.Button.builder(net.minecraft.network.chat.Component.literal("+10"),
                b -> setSize(size + 10)).bounds(left() + 78, y, 22, 20).build());
            final var take = net.minecraft.client.gui.components.Button.builder(net.minecraft.network.chat.Component.literal(
                "Take stored (" + LevelingStaffItem.storeTotal(stack) + ")"), b -> {
                    net.neoforged.neoforge.network.PacketDistributor.sendToServer(new StaffActionPayload(LevelingStaffItem.ACTION_TAKE));
                    onClose();
                }).bounds(left() + 120, y + 22, 100, 20).build();
            take.active = LevelingStaffItem.storeTotal(stack) > 0;
            addRenderableWidget(take);
            addRenderableWidget(net.minecraft.client.gui.components.Button.builder(net.minecraft.network.chat.Component.literal("Undo last"),
                b -> {
                    net.neoforged.neoforge.network.PacketDistributor.sendToServer(new WandPayload(action, mode, size, true));
                    onClose();
                }).bounds(left() + 120, y, 100, 20).build());
        }

        private void setSize(final int s)
        {
            size = Math.max(1, Math.min(BuildWand.MAX_SIZE, s));
            push();
        }

        private void push()
        {
            BuilderWandItem.setSettings(stack, new BuildWand.Settings(action, mode, size));
            net.neoforged.neoforge.network.PacketDistributor.sendToServer(new WandPayload(action, mode, size, false));
        }

        @Override
        public boolean mouseClicked(final double mx, final double my, final int button)
        {
            for (int i = 0; i < 4; i++)
            {
                if (inRow(mx, my, left(), i))
                {
                    action = i;
                    push();
                    return true;
                }
                if (inRow(mx, my, left() + 120, i))
                {
                    mode = i;
                    push();
                    return true;
                }
            }
            return super.mouseClicked(mx, my, button);
        }

        private boolean inRow(final double mx, final double my, final int x, final int i)
        {
            final int y = top() + 16 + i * 20;
            return mx >= x && mx < x + 100 && my >= y && my < y + 18;
        }

        @Override
        public void render(final net.minecraft.client.gui.GuiGraphics g, final int mx, final int my, final float pt)
        {
            super.render(g, mx, my, pt);
            g.fill(left() - 8, top() - 8, left() + 228, top() + 156, 0xFFEDE3C6);          // parchment panel
            g.drawString(font, "Action", left(), top() + 2, 0x302820, false);
            g.drawString(font, "Mode", left() + 120, top() + 2, 0x302820, false);
            for (int i = 0; i < 4; i++)
            {
                row(g, left(), i, BuildWand.ACTIONS[i], i == action);
                row(g, left() + 120, i, BuildWand.MODES[i], i == mode);
            }
            g.drawString(font, "Size", left(), top() + 98, 0x302820, false);
            g.drawCenteredString(font, mode == BuildWand.FILL ? "-" : String.valueOf(size), left() + 50, top() + 114, 0xFFFFFF);
            g.drawString(font, mode == BuildWand.FILL ? "Fill: corner to corner (up to " + BuildWand.MAX_SIZE + " per side)"
                : mode == BuildWand.AREA ? "Area: " + size + " x " + size : "Line: " + size + " long", left(), top() + 134, 0x504030, false);
            for (final var w : renderables)
            {
                w.render(g, mx, my, pt);
            }
            final ItemStack off = Minecraft.getInstance().player == null ? ItemStack.EMPTY : Minecraft.getInstance().player.getOffhandItem();
            g.drawString(font, off.isEmpty() ? "Off hand: empty" : "Off hand: " + off.getHoverName().getString(), left(), top() + 146, 0x504030, false);
        }

        private void row(final net.minecraft.client.gui.GuiGraphics g, final int x, final int i, final String text, final boolean on)
        {
            final int y = top() + 16 + i * 20;
            g.fill(x, y, x + 100, y + 18, on ? 0xFF3A9E9A : 0xFF3A3A3A);
            g.drawString(font, text, x + 4, y + 5, 0xFFFFFF, false);
        }

        @Override
        public boolean isPauseScreen()
        {
            return false;
        }
    }

    private static void renderWandPreview(final RenderLevelStageEvent event, final Minecraft mc, final ItemStack wand)
    {
        final net.minecraft.world.phys.HitResult aim = mc.player.pick(BuilderWandItem.RANGE, event.getPartialTick().getGameTimeDeltaPartialTick(true), false);
        if (!(aim instanceof net.minecraft.world.phys.BlockHitResult hit) || aim.getType() != net.minecraft.world.phys.HitResult.Type.BLOCK)
        {
            return;
        }
        final BuildWand.Settings s = BuilderWandItem.settings(wand);
        final BlockPos fill = s.mode() == BuildWand.FILL ? BuilderWandItem.fillCorner(wand) : null;
        final BlockPos[] box = BuildWand.bounds(mc.player, hit, s, fill);
        // big jobs: just the outline of the whole box (checking every block each frame would be too slow)
        // place / replace highlight only as many blocks as you carry (inventory + off hand)
        final ItemStack off = mc.player.getOffhandItem();
        final net.minecraft.world.level.block.Block offBlock = off.getItem() instanceof net.minecraft.world.item.BlockItem bi ? bi.getBlock() : null;
        final boolean uses = s.action() == BuildWand.PLACE || s.action() == BuildWand.REPLACE;
        final int carried = !uses || mc.player.isCreative() ? Integer.MAX_VALUE : offBlock == null ? 0 : mc.player.getInventory().countItem(off.getItem());
        final boolean limited = carried < BuildWand.volume(box);
        // small jobs: every block; limited by what you carry (up to 50k): exactly those; else the whole box
        final java.util.List<BlockPos> targets = BuildWand.volume(box) <= 2048 || (limited && carried <= 50_000)
            ? BuildWand.targets(mc.level, mc.player, hit, s, fill, Math.min(carried, 50_000), offBlock) : java.util.List.of();
        final float[] c = switch (s.action())
        {
            case BuildWand.PLACE -> new float[] {0.3f, 1.0f, 0.4f};
            case BuildWand.REPLACE -> new float[] {1.0f, 0.85f, 0.2f};
            case BuildWand.DESTROY -> new float[] {1.0f, 0.3f, 0.3f};
            default -> new float[] {0.4f, 0.7f, 1.0f};
        };
        final Vec3 cam = event.getCamera().getPosition();
        final PoseStack pose = event.getPoseStack();
        pose.pushPose();
        pose.translate(-cam.x, -cam.y, -cam.z);
        final MultiBufferSource.BufferSource buffers = mc.renderBuffers().bufferSource();
        final VertexConsumer lines = buffers.getBuffer(RenderType.lines());
        if (targets.size() <= 2048)
        {
            for (final BlockPos p : targets)
            {
                LevelRenderer.renderLineBox(pose, lines, new AABB(p).inflate(0.005), c[0], c[1], c[2], 0.9f);
            }
        }
        if (targets.size() > 2048)
        {
            // many blocks: one outline around the ones you can afford
            int x1 = Integer.MAX_VALUE, y1 = Integer.MAX_VALUE, z1 = Integer.MAX_VALUE, x2 = Integer.MIN_VALUE, y2 = Integer.MIN_VALUE, z2 = Integer.MIN_VALUE;
            for (final BlockPos p : targets)
            {
                x1 = Math.min(x1, p.getX()); y1 = Math.min(y1, p.getY()); z1 = Math.min(z1, p.getZ());
                x2 = Math.max(x2, p.getX()); y2 = Math.max(y2, p.getY()); z2 = Math.max(z2, p.getZ());
            }
            LevelRenderer.renderLineBox(pose, lines, new AABB(x1, y1, z1, x2 + 1, y2 + 1, z2 + 1).inflate(0.02), c[0], c[1], c[2], 1.0f);
        }
        else if (targets.isEmpty() && !limited && BuildWand.volume(box) > 2048)
        {
            // a big job you have enough blocks for: the outline of the whole box
            LevelRenderer.renderLineBox(pose, lines, AABB.encapsulatingFullBlocks(box[0], box[1]).inflate(0.02), c[0], c[1], c[2], 1.0f);
        }
        buffers.endBatch(RenderType.lines());
        pose.popPose();
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
        if (event.getStage() == RenderLevelStageEvent.Stage.AFTER_TRANSLUCENT_BLOCKS && mc.player.getMainHandItem().getItem() instanceof BuilderWandItem)
        {
            renderWandPreview(event, mc, mc.player.getMainHandItem());
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
