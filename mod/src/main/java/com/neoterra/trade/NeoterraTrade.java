package com.neoterra.trade;

import com.minecolonies.api.colony.buildings.registry.BuildingEntry;
import com.minecolonies.api.colony.jobs.registry.JobEntry;
import com.minecolonies.api.entity.citizen.Skill;
import com.minecolonies.api.items.ItemBlockHut;
import com.minecolonies.api.tileentities.MinecoloniesTileEntities;
import com.minecolonies.apiimp.CommonMinecoloniesAPIImpl;
import com.minecolonies.core.colony.buildings.modules.WorkerBuildingModule;
import com.minecolonies.core.colony.buildings.moduleviews.WorkerBuildingModuleView;
import com.minecolonies.core.colony.buildings.views.EmptyView;
import com.minecolonies.core.colony.jobs.views.DefaultJobView;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.Item;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.event.BlockEntityTypeAddBlocksEvent;
import net.neoforged.neoforge.event.BuildCreativeModeTabContentsEvent;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;
import net.neoforged.neoforge.registries.RegisterEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;


/**
 * Neoterra: the style packs (Neoterra, Hearthwood, Cascadia, Farmworks) plus the Trade Post –
 * a MineColonies hut whose Trade Courier links two of your colonies.
 */
@Mod(NeoterraTrade.MOD_ID)
public class NeoterraTrade
{
    public static final String MOD_ID = "neoterra";
    public static final Logger LOG = LoggerFactory.getLogger("neoterra");

    public static final DeferredRegister<BuildingEntry> BUILDINGS = DeferredRegister.create(CommonMinecoloniesAPIImpl.BUILDINGS, MOD_ID);
    public static final DeferredRegister<JobEntry>      JOBS      = DeferredRegister.create(CommonMinecoloniesAPIImpl.JOBS, MOD_ID);
    public static final DeferredRegister.Items          ITEMS     = DeferredRegister.createItems(MOD_ID);

    public static BlockHutTradePost TRADE_POST_BLOCK;

    public static final ResourceLocation COURIER_ID = id("tradecourier");

    public static final DeferredHolder<JobEntry, JobEntry> TRADE_COURIER = JOBS.register("tradecourier", () -> new JobEntry.Builder()
        .setJobProducer(JobTradeCourier::new)
        .setJobViewProducer(() -> DefaultJobView::new)
        .setRegistryName(COURIER_ID)
        .createJobEntry());

    public static final BuildingEntry.ModuleProducer<WorkerBuildingModule, WorkerBuildingModuleView> TRADE_WORK =
        new BuildingEntry.ModuleProducer<>("tradepost_work",
            () -> new WorkerBuildingModule(TRADE_COURIER.get(), Skill.Athletics, Skill.Stamina, true, b -> 1),
            () -> WorkerBuildingModuleView::new);

    public static final DeferredHolder<BuildingEntry, BuildingEntry> TRADE_POST = BUILDINGS.register(BuildingTradePost.SCHEMATIC, () -> new BuildingEntry.Builder()
        .setBuildingBlock(TRADE_POST_BLOCK)
        .setBuildingProducer(BuildingTradePost::new)
        .setBuildingViewProducer(() -> EmptyView::new)
        .setRegistryName(id(BuildingTradePost.SCHEMATIC))
        .addBuildingModuleProducer(TRADE_WORK)
        .createBuildingEntry());

    public static final DeferredItem<Item> LEDGER = ITEMS.register("trade_ledger", () -> new TradeLedgerItem(new Item.Properties().stacksTo(1)));

    public NeoterraTrade(final IEventBus modBus)
    {
        BUILDINGS.register(modBus);
        JOBS.register(modBus);
        ITEMS.register(modBus);
        modBus.addListener(this::onRegister);
        modBus.addListener(this::onBlockEntityBlocks);
        modBus.addListener(this::onCreativeTabs);
        SelfTest.register();
    }

    public static ResourceLocation id(final String path)
    {
        return ResourceLocation.fromNamespaceAndPath(MOD_ID, path);
    }

    /** The hut block and its item are created in the registry events, like MineColonies' own huts. */
    private void onRegister(final RegisterEvent event)
    {
        event.register(Registries.BLOCK, helper -> {
            TRADE_POST_BLOCK = new BlockHutTradePost();
            helper.register(TRADE_POST_BLOCK.getRegistryName(), TRADE_POST_BLOCK);
        });
        event.register(Registries.ITEM, helper ->
            helper.register(TRADE_POST_BLOCK.getRegistryName(), new ItemBlockHut(TRADE_POST_BLOCK, new Item.Properties())));
    }

    /** MineColonies' hut block entity only accepts its own hut blocks – add ours to the list. */
    private void onBlockEntityBlocks(final BlockEntityTypeAddBlocksEvent event)
    {
        event.modify(MinecoloniesTileEntities.BUILDING.get(), TRADE_POST_BLOCK);
    }

    private void onCreativeTabs(final BuildCreativeModeTabContentsEvent event)
    {
        if (event.getTabKey() == CreativeModeTabs.FUNCTIONAL_BLOCKS)
        {
            event.accept(TRADE_POST_BLOCK);
        }
        if (event.getTabKey() == CreativeModeTabs.TOOLS_AND_UTILITIES)
        {
            event.accept(LEDGER.get());
        }
    }
}
