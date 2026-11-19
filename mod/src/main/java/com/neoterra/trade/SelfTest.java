package com.neoterra.trade;

import com.minecolonies.api.blocks.ModBlocks;
import com.minecolonies.api.colony.IColony;
import com.minecolonies.api.colony.IColonyManager;
import com.minecolonies.api.colony.buildings.IBuilding;
import com.minecolonies.api.colony.requestsystem.request.IRequest;
import com.minecolonies.api.colony.requestsystem.requestable.Stack;
import com.minecolonies.api.colony.requestsystem.token.IToken;
import com.minecolonies.api.tileentities.AbstractTileEntityColonyBuilding;
import com.mojang.authlib.GameProfile;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.levelgen.Heightmap;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.common.util.FakePlayerFactory;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import net.neoforged.neoforge.items.IItemHandler;
import net.neoforged.neoforge.items.ItemHandlerHelper;

import java.util.UUID;

/**
 * Development self-test, only active with -Dneoterra.selftest=true: builds two colonies with a
 * Trade Post each and pushes one request through the whole trade loop, then stops the server.
 */
final class SelfTest
{
    private int        tick = 0;
    private int        stage = 0;
    private IColony    a, b;
    private BuildingTradePost postA, postB;
    private IBuilding  hallA;
    private IToken<?>  token;

    static void register()
    {
        if (Boolean.getBoolean("neoterra.selftest"))
        {
            NeoForge.EVENT_BUS.register(new SelfTest());
        }
    }

    @net.neoforged.bus.api.SubscribeEvent
    public void onTick(final ServerTickEvent.Post event)
    {
        tick++;
        if (tick < 60 || stage < 0)
        {
            return;
        }
        final ServerLevel level = event.getServer().overworld();
        try
        {
            step(level);
        }
        catch (final Throwable t)
        {
            NeoterraTrade.LOG.error("SELFTEST FAIL (exception in stage " + stage + ")", t);
            finish(level, false);
        }
        if (tick > 6000 && stage >= 0)
        {
            NeoterraTrade.LOG.error("SELFTEST FAIL (timeout in stage {})", stage);
            finish(level, false);
        }
    }

    private void step(final ServerLevel level)
    {
        switch (stage)
        {
            case 0 ->
            {
                a = colony(level, new BlockPos(0, 0, 0), "Alpha");
                b = colony(level, new BlockPos(400, 0, 0), "Beta");
                hallA = hut(level, a, ModBlocks.blockHutTownHall, new BlockPos(0, 0, 0));
                postA = (BuildingTradePost) hut(level, a, NeoterraTrade.TRADE_POST_BLOCK, new BlockPos(8, 0, 0));
                hut(level, b, ModBlocks.blockHutTownHall, new BlockPos(400, 0, 0));
                postB = (BuildingTradePost) hut(level, b, NeoterraTrade.TRADE_POST_BLOCK, new BlockPos(408, 0, 0));
                postA.link(b, postB.getPosition());
                postB.link(a, postA.getPosition());
                log("colonies %d and %d, posts linked: %s", a.getID(), b.getID(), postA.getPartner() == postB && postB.getPartner() == postA);
                token = hallA.createRequest(new Stack(new ItemStack(Items.STONE_BRICKS), 16, 16), false);
                log("town hall of Alpha requests 16 stone bricks: %s", token);
                stage = 1;
            }
            case 1 ->
            {
                if (tick % 20 == 0)
                {
                    postA.onColonyTick(a);
                    final IRequest<?> r = a.getRequestManager().getRequestForToken(token);
                    log("request state %s, Beta orders %d", r.getState(), postB.openOrders());
                    if (postB.openOrders() > 0)
                    {
                        stage = 2;
                    }
                }
            }
            case 2 ->
            {
                final IItemHandler h = postB.getItemHandlerCap();
                log("post handler %s slots %d, te %s", h == null ? null : h.getClass().getSimpleName(), h == null ? -1 : h.getSlots(), postB.getTileEntity());
                final ItemStack rest = ItemHandlerHelper.insertItemStacked(h, new ItemStack(Items.STONE_BRICKS, 16), false);
                log("Beta's stonemason 'delivered' 16 stone bricks to Beta's post (left over: %d)", rest.getCount());
                final BuildingTradePost.Order order = postB.nextReadyOrder();
                log("ready order: %s", order != null);
                log("dispatched: %s, in transit %d", order != null && postB.dispatch(order, 40), postB.inTransit());
                stage = 3;
            }
            case 3 ->
            {
                if (tick % 20 == 0)
                {
                    postB.onColonyTick(b);
                    if (postB.inTransit() == 0)
                    {
                        final IRequest<?> r = a.getRequestManager().getRequestForToken(token);
                        int bricks = 0;
                        final IItemHandler h = hallA.getItemHandlerCap();
                        for (int i = 0; i < h.getSlots(); i++)
                        {
                            if (h.getStackInSlot(i).is(Items.STONE_BRICKS))
                            {
                                bricks += h.getStackInSlot(i).getCount();
                            }
                        }
                        log("arrived: Alpha town hall holds %d stone bricks, request state %s", bricks, r == null ? "gone" : r.getState());
                        finish(level, bricks == 16);
                    }
                }
            }
            default -> { }
        }
    }

    private IColony colony(final ServerLevel level, final BlockPos at, final String name)
    {
        final FakePlayer owner = FakePlayerFactory.get(level, new GameProfile(UUID.nameUUIDFromBytes(name.getBytes()), name));
        final BlockPos pos = ground(level, at);
        return IColonyManager.getInstance().createColony(level, pos, owner, name, "Farmworks");
    }

    private IBuilding hut(final ServerLevel level, final IColony colony, final Block block, final BlockPos at)
    {
        final BlockPos pos = ground(level, at).above();
        level.setBlock(pos, block.defaultBlockState(), 3);
        final AbstractTileEntityColonyBuilding te = (AbstractTileEntityColonyBuilding) level.getBlockEntity(pos);
        final IBuilding building = colony.getServerBuildingManager().addNewBuilding(te, level);
        building.setBuildingLevel(1);
        return building;
    }

    private static BlockPos ground(final ServerLevel level, final BlockPos at)
    {
        level.setChunkForced(at.getX() >> 4, at.getZ() >> 4, true);
        level.getChunk(at);
        return new BlockPos(at.getX(), level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, at.getX(), at.getZ()), at.getZ());
    }

    private void finish(final ServerLevel level, final boolean pass)
    {
        stage = -1;
        NeoterraTrade.LOG.info(pass ? "SELFTEST PASS" : "SELFTEST FAIL");
        level.getServer().halt(false);
    }

    private static void log(final String fmt, final Object... args)
    {
        NeoterraTrade.LOG.info("[selftest] " + String.format(fmt, args));
    }
}
