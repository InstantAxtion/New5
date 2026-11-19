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
    private BuildingSupplyDepot depot;
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

    private void step(final ServerLevel level) throws ReflectiveOperationException
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
                        if (bricks != 16)
                        {
                            finish(level, false);
                            return;
                        }
                        stage = 4;
                    }
                }
            }
            case 4 ->
            {
                // Supply Depot: a request nobody makes is crafted from delivered ingredients
                postA.unlink();
                postB.unlink();
                depot = (BuildingSupplyDepot) hut(level, a, NeoterraTrade.SUPPLY_DEPOT_BLOCK, new BlockPos(0, 0, 10));
                token = hallA.createRequest(new Stack(new ItemStack(Items.OAK_SLAB), 12, 12), false);
                log("town hall of Alpha requests 12 oak slabs");
                stage = 5;
            }
            case 5 ->
            {
                if (tick % 20 == 0)
                {
                    final int taken = depot.planOrders();
                    log("depot orders %d (new %d)", depot.openOrders(), taken);
                    if (depot.openOrders() > 0)
                    {
                        final ItemStack rest = ItemHandlerHelper.insertItemStacked(depot.getItemHandlerCap(), new ItemStack(Items.OAK_PLANKS, 6), false);
                        final BuildingSupplyDepot.Order o = depot.nextCraftable();
                        log("6 oak planks delivered (left %d), craftable: %s", rest.getCount(), o != null);
                        final boolean crafted = o != null && depot.craft(o);
                        final IBuilding target = o == null ? null : depot.deliveryTarget(o);
                        log("crafted %s, delivering to %s", crafted, target == null ? null : target.getSchematicName());
                        if (o != null && target != null)
                        {
                            depot.deliver(o, target);
                        }
                        final int slabs = countIn(hallA, Items.OAK_SLAB);
                        final IRequest<?> r = a.getRequestManager().getRequestForToken(token);
                        log("Alpha town hall holds %d oak slabs, request %s", slabs, r == null ? "gone" : r.getState());
                        if (slabs != 12)
                        {
                            finish(level, false);
                            return;
                        }
                        stage = 6;
                    }
                }
            }
            case 6 ->
            {
                // Grand Project bonus + builder speed through research effects
                final IBuilding cathedral = hut(level, a, NeoterraTrade.WONDER_BLOCKS.get(WonderType.CATHEDRAL), new BlockPos(-12, 0, 0));
                cathedral.setBuildingLevel(2);
                ColonyBoosts.applyBoosts(a);
                final var fx = a.getResearchManager().getResearchEffects();
                final double happy = fx.getEffectStrength(com.minecolonies.api.research.util.ResearchConstants.HAPPINESS);
                final double place = fx.getEffectStrength(com.minecolonies.api.research.util.ResearchConstants.BLOCK_PLACE_SPEED);
                log("cathedral level 2: happiness +%.2f, block place speed untouched: %.3f", happy, place);
                cathedral.setBuildingLevel(0);
                ColonyBoosts.applyBoosts(a);
                final double after = fx.getEffectStrength(com.minecolonies.api.research.util.ResearchConstants.HAPPINESS);
                log("cathedral gone: happiness +%.2f", after);
                if (!(Math.abs(happy - 0.06) < 1e-6 && place == 0 && after == 0))
                {
                    finish(level, false);
                    return;
                }
                // up-front materials: a builder with a calculated material list asks for all of it at once
                final var builder = (com.minecolonies.core.colony.buildings.AbstractBuildingStructureBuilder)
                    hut(level, a, ModBlocks.blockHutBuilder, new BlockPos(12, 0, 10));
                depot.setStructurePack("Farmworks");
                depot.setBlueprintPath("trade/supplydepot1.blueprint");
                final var wo = com.minecolonies.core.colony.workorders.WorkOrderBuilding.create(
                    com.minecolonies.api.colony.workorders.WorkOrderType.UPGRADE, depot);
                a.getWorkManager().addWorkOrder(wo, false);
                wo.setClaimedBy(builder.getID());
                builder.setWorkOrder(wo);
                wo.setRequested(true);
                final java.util.Map<String, com.minecolonies.core.colony.buildings.utils.BuildingBuilderResource> needed = neededMap(builder);
                needed.put("STONE_BRICKS", new com.minecolonies.core.colony.buildings.utils.BuildingBuilderResource(new ItemStack(Items.STONE_BRICKS), 200));
                needed.put("GLASS", new com.minecolonies.core.colony.buildings.utils.BuildingBuilderResource(new ItemStack(Items.GLASS), 40));
                needed.put("OAK_LOG", new com.minecolonies.core.colony.buildings.utils.BuildingBuilderResource(new ItemStack(Items.OAK_LOG), 8));
                ItemHandlerHelper.insertItemStacked(builder.getItemHandlerCap(), new ItemStack(Items.OAK_LOG, 8), false);
                final int made = ColonyBoosts.requestUpfront(a);
                final int again = ColonyBoosts.requestUpfront(a);
                final StringBuilder sb = new StringBuilder();
                builder.getOpenRequestsOfType(-1, com.google.common.reflect.TypeToken.of(Stack.class))
                    .forEach(r -> sb.append(r.getRequest().getCount()).append("x").append(r.getRequest().getStack().getItem()).append(' '));
                log("builder up-front requests: %d made, %d on second pass; open: %s", made, again, sb.toString().trim());
                if (made != 2 || again != 0)
                {
                    finish(level, false);
                    return;
                }
                finish(level, checkBlueprints(level) && checkResearch());
            }
            default -> { }
        }
    }

    /** The University research line is in MineColonies' research tree with the crafting-speed effect. */
    private static boolean checkResearch()
    {
        final var tree = com.minecolonies.api.research.IGlobalResearchTree.getInstance();
        final net.minecraft.resources.ResourceLocation branch = net.minecraft.resources.ResourceLocation.fromNamespaceAndPath("minecolonies", "technology");
        final double[] expect = {0.05, 0.10, 0.15};
        final String[] names = {"efficientbenches", "workshoprhythm", "masterartisans"};
        boolean ok = true;
        for (int i = 0; i < names.length; i++)
        {
            final var id = NeoterraTrade.id("technology/" + names[i]);
            final var r = tree.hasResearch(branch, id) ? tree.getResearch(branch, id) : null;
            if (r == null)
            {
                log("research %s missing", id);
                ok = false;
                continue;
            }
            final double strength = r.getEffects().stream().filter(e -> e.getId().equals(ColonyBoosts.CRAFTING_SPEED)).mapToDouble(e -> e.getEffect()).findFirst().orElse(-1);
            log("research %s: depth %d, parent %s, crafting speed +%.0f%%", names[i], r.getDepth(), r.getParent(), strength * 100);
            ok &= Math.abs(strength - expect[i]) < 1e-9 && r.getDepth() == i + 1;
        }
        return ok;
    }

    /** Every hut blueprint of ours loads through Structurize, with the right hut block and (wonders) two wing huts. */
    private static boolean checkBlueprints(final ServerLevel level)
    {
        boolean ok = true;
        final java.util.List<String[]> list = new java.util.ArrayList<>();
        for (int l = 1; l <= 5; l++)
        {
            list.add(new String[] {"Farmworks", "trade/tradepost" + l, "blockhuttradepost", "0"});
            list.add(new String[] {"Farmworks", "trade/supplydepot" + l, "blockhutsupplydepot", "0"});
            for (final String pack : new String[] {"Neoterra", "Hearthwood", "Cascadia"})
            {
                for (final WonderType t : WonderType.values())
                {
                    list.add(new String[] {pack, "wonders/" + t.id + l, "blockhut" + t.id, "2"});
                    list.add(new String[] {pack, "wonders/" + t.id + "wing" + l, "blockhutwonderwing", "0"});
                }
            }
        }
        int checked = 0;
        for (final String[] e : list)
        {
            final com.ldtteam.structurize.blueprints.v1.Blueprint bp =
                com.ldtteam.structurize.storage.StructurePacks.getBlueprint(e[0], e[1] + ".blueprint", level.registryAccess());
            if (bp == null)
            {
                log("blueprint %s/%s did not load", e[0], e[1]);
                ok = false;
                continue;
            }
            final var info = bp.getBlockInfoAsMap();
            final var anchor = info.get(bp.getPrimaryBlockOffset());
            final String anchorId = anchor == null ? "none" : net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(anchor.getState().getBlock()).toString();
            final long wings = info.values().stream()
                .filter(b -> b.getState().getBlock() == NeoterraTrade.WING_BLOCK && b.getTileEntityData() != null).count();
            final long expectWings = Long.parseLong(e[3]);
            if (!anchorId.equals("neoterra:" + e[2]) || (expectWings > 0 && wings != expectWings))
            {
                log("blueprint %s/%s: anchor %s, wing huts %d", e[0], e[1], anchorId, wings);
                ok = false;
            }
            checked++;
        }
        log("%d hut blueprints loaded through Structurize, all anchors right: %s", checked, ok);
        return ok;
    }

    @SuppressWarnings("unchecked")
    private static java.util.Map<String, com.minecolonies.core.colony.buildings.utils.BuildingBuilderResource> neededMap(
        final com.minecolonies.core.colony.buildings.AbstractBuildingStructureBuilder builder) throws ReflectiveOperationException
    {
        final var module = builder.getFirstModuleOccurance(com.minecolonies.core.colony.buildings.modules.BuildingResourcesModule.class);
        final java.lang.reflect.Field f = module.getClass().getDeclaredField("neededResources");
        f.setAccessible(true);
        return (java.util.Map<String, com.minecolonies.core.colony.buildings.utils.BuildingBuilderResource>) f.get(module);
    }

    private static int countIn(final IBuilding b, final net.minecraft.world.item.Item item)
    {
        int n = 0;
        final IItemHandler h = b.getItemHandlerCap();
        for (int i = 0; i < h.getSlots(); i++)
        {
            if (h.getStackInSlot(i).is(item))
            {
                n += h.getStackInSlot(i).getCount();
            }
        }
        return n;
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
