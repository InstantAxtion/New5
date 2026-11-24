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
                finish(level, checkBlueprints(level) & checkResearch() & checkFreeFastResearch() & checkFreePlacement(level) & checkEntities(level) & checkFlatten(level) & checkWand(level));
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

    /** All research is free (no item costs) and 10x faster (branch base time 72 -> 7 per level-1 research). */
    private static boolean checkFreeFastResearch()
    {
        final var tree = com.minecolonies.api.research.IGlobalResearchTree.getInstance();
        boolean ok = true;
        int branches = 0;
        for (final var branch : tree.getBranches())
        {
            final var data = tree.getBranchData(branch);
            final int t = data.getBaseTime(1);
            branches++;
            if (t > 8)
            {
                log("research branch %s still slow: %d", branch, t);
                ok = false;
            }
        }
        final String[][] samples = {{"combat", "accuracy"}, {"civilian", "academic"}, {"technology", "ability"}};
        int checked = 0;
        for (final String[] smp : samples)
        {
            final var br = net.minecraft.resources.ResourceLocation.fromNamespaceAndPath("minecolonies", smp[0]);
            final var id = net.minecraft.resources.ResourceLocation.fromNamespaceAndPath("minecolonies", smp[0] + "/" + smp[1]);
            if (tree.hasResearch(br, id))
            {
                checked++;
                if (!tree.getResearch(br, id).getCostList().isEmpty())
                {
                    log("research %s still costs items", id);
                    ok = false;
                }
            }
        }
        final var tech = net.minecraft.resources.ResourceLocation.fromNamespaceAndPath("minecolonies", "technology");
        final var own = NeoterraTrade.id("technology/efficientbenches");
        if (tree.hasResearch(tech, own) && !tree.getResearch(tech, own).getCostList().isEmpty())
        {
            ok = false;
        }
        log("research: %d branches 10x faster, %d sampled researches free: %s", branches, checked, ok && checked > 0);
        return ok && checked > 0;
    }

    /** Leveling Staff: refuses with a chest in the way or without enough fill, then flattens a hill, a pit and a tree. */
    private boolean checkFlatten(final ServerLevel level)
    {
        final net.minecraft.world.level.block.state.BlockState stone = net.minecraft.world.level.block.Blocks.STONE.defaultBlockState();
        final net.minecraft.world.level.block.state.BlockState air = net.minecraft.world.level.block.Blocks.AIR.defaultBlockState();
        final int x0 = 1500, z0 = 1500;
        final int g = ground(level, new BlockPos(x0 + 5, 0, z0 + 5)).getY() + 2;
        for (int x = x0 - 2; x < x0 + 12; x++)
        {
            for (int z = z0 - 2; z < z0 + 12; z++)
            {
                level.setChunkForced(x >> 4, z >> 4, true);
                for (int y = g - 8; y <= g + 12; y++)
                {
                    level.setBlock(new BlockPos(x, y, z), y <= g ? stone : air, 2);
                }
            }
        }
        // hill (4 x 10 x 3 = 120 stone), pit (4 x 10 x 5 = 200 cells), a small tree
        for (int x = x0; x < x0 + 4; x++)
            for (int z = z0; z < z0 + 10; z++)
                for (int y = g + 1; y <= g + 3; y++)
                    level.setBlock(new BlockPos(x, y, z), stone, 2);
        for (int x = x0 + 6; x < x0 + 10; x++)
            for (int z = z0; z < z0 + 10; z++)
                for (int y = g - 4; y <= g; y++)
                    level.setBlock(new BlockPos(x, y, z), air, 2);
        for (int y = g + 1; y <= g + 4; y++)
            level.setBlock(new BlockPos(x0 + 4, y, z0 + 5), net.minecraft.world.level.block.Blocks.OAK_LOG.defaultBlockState(), 2);
        final BlockPos sign = new BlockPos(x0 + 1, g + 4, z0 + 1);
        level.setBlock(sign, net.minecraft.world.level.block.Blocks.OAK_SIGN.defaultBlockState(), 3);
        final java.util.Map<BlockPos, net.minecraft.world.level.block.state.BlockState> before = new java.util.HashMap<>();
        final BlockPos chest = new BlockPos(x0 + 5, g + 1, z0 + 2);
        level.setBlock(chest, net.minecraft.world.level.block.Blocks.CHEST.defaultBlockState(), 3);
        final FakePlayer p = FakePlayerFactory.get(level, new GameProfile(UUID.nameUUIDFromBytes("Leveler".getBytes()), "Leveler"));
        p.getInventory().clearContent();
        // second corner at a different height: the ground level is still the first corner's
        final BlockPos a = new BlockPos(x0, g, z0), b = new BlockPos(x0 + 9, g + 5, z0 + 9);
        final Flattening.Plan withChest = Flattening.plan(level, p, a, b);
        level.setBlock(chest, air, 3);
        final Flattening.Plan noFill = Flattening.plan(level, p, a, b);
        p.getInventory().add(new ItemStack(Items.DIRT, 64));
        p.getInventory().add(new ItemStack(Items.DIRT, 36));
        for (int x = x0 - 1; x <= x0 + 10; x++)
            for (int z = z0 - 1; z <= z0 + 10; z++)
                for (int y = g - 6; y <= g + 8; y++)
                    before.put(new BlockPos(x, y, z), level.getBlockState(new BlockPos(x, y, z)));
        final Flattening.Plan ok = Flattening.plan(level, p, a, b);
        if (ok.refusal() == null)
        {
            Flattening.start(ok, p);
            Flattening.runAll();
        }
        int flat = 0, filled = 0;
        for (int x = x0; x < x0 + 10; x++)
        {
            for (int z = z0; z < z0 + 10; z++)
            {
                boolean col = level.getBlockState(new BlockPos(x, g, z)).isSolid();
                for (int y = g + 1; y <= g + 8; y++)
                {
                    col &= level.getBlockState(new BlockPos(x, y, z)).isAir();
                }
                flat += col ? 1 : 0;
                if (x >= x0 + 6)
                {
                    for (int y = g - 4; y <= g; y++)
                    {
                        filled += level.getBlockState(new BlockPos(x, y, z)).isSolid() ? 1 : 0;
                    }
                }
            }
        }
        final int dirtLeft = p.getInventory().countItem(Items.DIRT);
        final int logs = p.getInventory().countItem(Items.OAK_LOG);
        // undo: land, sign and items come back
        final String undoWhy = Flattening.undo(p);
        Flattening.runAll();
        int same = 0;
        for (final var e : before.entrySet())
        {
            same += level.getBlockState(e.getKey()).equals(e.getValue()) ? 1 : 0;
        }
        final boolean signBack = level.getBlockEntity(sign) instanceof net.minecraft.world.level.block.entity.SignBlockEntity;
        final int dirtAfterUndo = p.getInventory().countItem(Items.DIRT), logsAfterUndo = p.getInventory().countItem(Items.OAK_LOG);
        final String again = Flattening.undo(p);
        // area size: 192 is allowed, 193 is not
        final Flattening.Plan big = Flattening.plan(level, p, new BlockPos(x0 + 2000, g, z0), new BlockPos(x0 + 2000 + 191, g, z0 + 191));
        final Flattening.Plan tooBig = Flattening.plan(level, p, new BlockPos(x0, g, z0), new BlockPos(x0 + 192, g, z0));
        log("leveling staff undo: %s, blocks restored %d/%d, sign back %s, dirt %d, logs %d, second undo -> %s; 192 wide -> %s; 193 wide -> %s",
            undoWhy, same, before.size(), signBack, dirtAfterUndo, logsAfterUndo, again,
            big.refusal() == null ? "allowed" : big.refusal(), tooBig.refusal());
        final boolean undoOk = undoWhy == null && same == before.size() && signBack && dirtAfterUndo == 100 && logsAfterUndo == 0
            && again != null && (big.refusal() == null || !big.refusal().contains("at most")) && tooBig.refusal() != null && tooBig.refusal().contains("at most");
        log("leveling staff: chest -> %s | no fill -> %s | fill needed %d, flat columns %d/100, pit cells filled %d/200, dirt left %d, oak logs %d",
            withChest.refusal(), noFill.refusal(), ok.fillNeeded(), flat, filled, dirtLeft, logs);
        return withChest.refusal() != null && withChest.refusal().contains("container") && noFill.refusal() != null
            && ok.refusal() == null && ok.ground() == g && ok.fillNeeded() == 200 && flat == 100 && filled == 200 && dirtLeft == 20 && logs == 4 && undoOk;
    }

    /** Builder's Wand: place / replace / destroy / use in different modes; inventory first, off hand last; undo. */
    private boolean checkWand(final ServerLevel level)
    {
        final int x0 = 1800, z0 = 1800;
        final int g = ground(level, new BlockPos(x0 + 6, 0, z0 + 6)).getY() + 2;
        for (int x = x0 - 2; x < x0 + 14; x++)
            for (int z = z0 - 2; z < z0 + 14; z++)
            {
                level.setChunkForced(x >> 4, z >> 4, true);
                for (int y = g - 2; y <= g + 6; y++)
                    level.setBlock(new BlockPos(x, y, z), y <= g ? net.minecraft.world.level.block.Blocks.STONE.defaultBlockState()
                        : net.minecraft.world.level.block.Blocks.AIR.defaultBlockState(), 2);
            }
        final FakePlayer p = FakePlayerFactory.get(level, new GameProfile(UUID.nameUUIDFromBytes("Wand".getBytes()), "Wand"));
        p.getInventory().clearContent();
        p.setYRot(0);
        p.setXRot(0);
        p.getInventory().add(new ItemStack(Items.STONE_BRICKS, 64));
        p.setItemInHand(net.minecraft.world.InteractionHand.OFF_HAND, new ItemStack(Items.STONE_BRICKS, 10));
        final BlockPos c = new BlockPos(x0 + 3, g, z0 + 3);
        final java.util.function.Function<BlockPos, net.minecraft.world.phys.BlockHitResult> top = q ->
            new net.minecraft.world.phys.BlockHitResult(net.minecraft.world.phys.Vec3.atCenterOf(q).add(0, 0.5, 0), net.minecraft.core.Direction.UP, q, false);
        // 1. place a 3x3 area on the floor
        final String m1 = BuildWand.apply(level, p, top.apply(c), new BuildWand.Settings(BuildWand.PLACE, BuildWand.AREA, 3));
        int placed = 0;
        for (int dx = -1; dx <= 1; dx++)
            for (int dz = -1; dz <= 1; dz++)
                placed += level.getBlockState(c.offset(dx, 1, dz)).is(net.minecraft.world.level.block.Blocks.STONE_BRICKS) ? 1 : 0;
        final int inv1 = p.getInventory().countItem(Items.STONE_BRICKS) - p.getOffhandItem().getCount(), off1 = p.getOffhandItem().getCount();
        // 2. replace a row of 5 (3 bricks there) with oak planks from the off hand
        p.setItemInHand(net.minecraft.world.InteractionHand.OFF_HAND, new ItemStack(Items.OAK_PLANKS, 16));
        final String m2 = BuildWand.apply(level, p, top.apply(c.above()), new BuildWand.Settings(BuildWand.REPLACE, BuildWand.ROW_COLUMN, 5));
        int planks = 0;
        for (int dz = -2; dz <= 2; dz++)
            planks += level.getBlockState(c.offset(0, 1, dz)).is(net.minecraft.world.level.block.Blocks.OAK_PLANKS) ? 1 : 0;
        final int bricksBack = p.getInventory().countItem(Items.STONE_BRICKS);
        // 3. destroy 2 deep (a brick and the stone under it)
        final String m3 = BuildWand.apply(level, p, top.apply(c.offset(1, 1, 1)), new BuildWand.Settings(BuildWand.DESTROY, BuildWand.DIRECTION, 2));
        final boolean dug = level.getBlockState(c.offset(1, 1, 1)).isAir() && level.getBlockState(c.offset(1, 0, 1)).isAir();
        // 4. fill corner to corner: a 4 x 2 x 4 block of bricks (two clicks with the wand)
        p.setItemInHand(net.minecraft.world.InteractionHand.OFF_HAND, new ItemStack(Items.STONE_BRICKS, 64));
        final ItemStack wand = new ItemStack(NeoterraTrade.BUILDER_WAND.get());
        final BuildWand.Settings fillS = new BuildWand.Settings(BuildWand.PLACE, BuildWand.FILL, 4);
        final String m4a = BuildWand.apply(level, p, top.apply(new BlockPos(x0 + 8, g, z0 + 8)), fillS, wand);
        final String m4 = m4a + " / " + BuildWand.apply(level, p, top.apply(new BlockPos(x0 + 11, g + 1, z0 + 11)), fillS, wand);
        int filled = 0;
        for (int x = x0 - 2; x < x0 + 14; x++)
            for (int z = z0 - 2; z < z0 + 14; z++)
                for (int y = g + 1; y <= g + 2; y++)
                    filled += level.getBlockState(new BlockPos(x, y, z)).is(net.minecraft.world.level.block.Blocks.STONE_BRICKS) ? 1 : 0;
        // 5. use: a shovel makes a path on a row of 3 grass blocks; then undo it
        for (int dx = 0; dx < 3; dx++)
            level.setBlock(new BlockPos(x0 + dx, g, z0 + 11), net.minecraft.world.level.block.Blocks.GRASS_BLOCK.defaultBlockState(), 3);
        p.setYRot(-90);   // looking east: the row runs along x
        p.setItemInHand(net.minecraft.world.InteractionHand.OFF_HAND, new ItemStack(Items.IRON_SHOVEL));
        final String m5 = BuildWand.apply(level, p, top.apply(new BlockPos(x0 + 1, g, z0 + 11)), new BuildWand.Settings(BuildWand.USE, BuildWand.ROW_COLUMN, 3));
        int paths = 0;
        for (int dx = 0; dx < 3; dx++)
            paths += level.getBlockState(new BlockPos(x0 + dx, g, z0 + 11)).is(net.minecraft.world.level.block.Blocks.DIRT_PATH) ? 1 : 0;
        final String m6 = BuildWand.undo(p);
        int grass = 0;
        for (int dx = 0; dx < 3; dx++)
            grass += level.getBlockState(new BlockPos(x0 + dx, g, z0 + 11)).is(net.minecraft.world.level.block.Blocks.GRASS_BLOCK) ? 1 : 0;
        log("builder's wand: place area '%s' -> %d placed, inventory bricks %d (64-9), off hand %d (untouched) | replace row '%s' -> %d planks, bricks back %d | destroy '%s' -> %s | fill '%s' -> %d bricks on the floor | use '%s' -> %d paths | undo '%s' -> %d grass back",
            m1, placed, inv1, off1, m2, planks, bricksBack, m3, dug, m4, filled, m5, paths, m6, grass);
        return placed == 9 && inv1 == 55 && off1 == 10 && planks == 3 && bricksBack == 58 && dug && filled == 9 - 3 - 1 + 32 && paths == 3 && grass == 3;
    }

    /** Item frames and armour stands in the player house survive loading through Structurize. */
    private static boolean checkEntities(final ServerLevel level)
    {
        boolean ok = true;
        for (final String pack : new String[] {"Neoterra", "Hearthwood", "Cascadia"})
        {
            final com.ldtteam.structurize.blueprints.v1.Blueprint bp =
                com.ldtteam.structurize.storage.StructurePacks.getBlueprint(pack, "decorations/housing/playerhouse5.blueprint", level.registryAccess());
            int frames = 0, stands = 0;
            if (bp != null && bp.getEntities() != null)
            {
                for (final net.minecraft.nbt.CompoundTag e : bp.getEntities())
                {
                    final String id = e.getString("id");
                    frames += id.contains("item_frame") ? 1 : 0;
                    stands += id.equals("minecraft:armor_stand") ? 1 : 0;
                }
            }
            log("%s player house L5: %d item frames, %d armour stands", pack, frames, stands);
            ok &= frames > 0 && stands > 0;
        }
        return ok;
    }

    /** A hut is placed with the build tool without its hut block in the inventory; a refused placement leaves nothing behind. */
    private boolean checkFreePlacement(final ServerLevel level)
    {
        final String path = "craftsmanship/luxury/baker1.blueprint";
        final com.ldtteam.structurize.blueprints.v1.Blueprint bp =
            com.ldtteam.structurize.storage.StructurePacks.getBlueprint("Neoterra", path, level.registryAccess());
        if (bp == null)
        {
            log("free placement: %s did not load", path);
            return false;
        }
        final FakePlayer owner = FakePlayerFactory.get(level, new GameProfile(UUID.nameUUIDFromBytes("Alpha".getBytes()), "Alpha"));
        owner.getInventory().clearContent();
        final var handler = new com.minecolonies.core.placementhandlers.main.SurvivalHandler();
        // inside Alpha's colony
        final BlockPos inside = ground(level, new BlockPos(24, 0, 24)).above();
        handler.handle(bp, "Neoterra", path, false, level, owner, inside, com.ldtteam.structurize.api.RotationMirror.NONE);
        final boolean placed = a.getServerBuildingManager().getBuilding(inside) != null;
        final int leftIn = owner.getInventory().countItem(net.minecraft.world.item.Item.byBlock(
            bp.getBlockState(bp.getPrimaryBlockOffset()).getBlock()));
        // far outside any colony: refused, and the loaned hut block is taken back
        final BlockPos outside = ground(level, new BlockPos(3000, 0, 3000)).above();
        final com.ldtteam.structurize.blueprints.v1.Blueprint bp2 =
            com.ldtteam.structurize.storage.StructurePacks.getBlueprint("Neoterra", path, level.registryAccess());
        handler.handle(bp2, "Neoterra", path, false, level, owner, outside, com.ldtteam.structurize.api.RotationMirror.NONE);
        int items = 0;
        for (int i = 0; i < owner.getInventory().getContainerSize(); i++)
        {
            items += owner.getInventory().getItem(i).getCount();
        }
        log("free placement: baker placed without a hut block: %s (hut blocks left %d); refused placement leaves %d items", placed, leftIn, items);
        return placed && leftIn == 0 && items == 0;
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
                    list.add(new String[] {pack, "monuments/" + t.id + l, "blockhut" + t.id, "2"});
                    list.add(new String[] {pack, "monuments/" + t.id + "wing" + l, "blockhutwonderwing", "0"});
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
