package com.neoterra.trade;

import com.minecolonies.api.blocks.AbstractBlockHut;
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
import net.minecraft.world.level.block.Block;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import net.neoforged.fml.config.ModConfig;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.BlockEntityTypeAddBlocksEvent;
import net.neoforged.neoforge.event.BuildCreativeModeTabContentsEvent;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;
import net.neoforged.neoforge.registries.RegisterEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;

/**
 * Neoterra: the style packs (Neoterra, Hearthwood, Cascadia, Farmworks) plus MineColonies add-ons:
 * <ul>
 *   <li>Trade Post + Trade Courier – trade between two of your colonies;</li>
 *   <li>Supply Depot + Quartermaster – crafts requested items nobody else makes;</li>
 *   <li>builder speed and up-front material requests (config);</li>
 *   <li>four Grand Projects with wing huts and colony-wide bonuses.</li>
 * </ul>
 */
@Mod(NeoterraTrade.MOD_ID)
public class NeoterraTrade
{
    public static final String MOD_ID = "neoterra";
    public static final Logger LOG = LoggerFactory.getLogger("neoterra");

    public static final DeferredRegister<BuildingEntry> BUILDINGS = DeferredRegister.create(CommonMinecoloniesAPIImpl.BUILDINGS, MOD_ID);
    public static final DeferredRegister<JobEntry>      JOBS      = DeferredRegister.create(CommonMinecoloniesAPIImpl.JOBS, MOD_ID);
    public static final DeferredRegister.Items          ITEMS     = DeferredRegister.createItems(MOD_ID);

    // hut blocks are created in the block registry event (like MineColonies' own)
    public static BlockHutTradePost                      TRADE_POST_BLOCK;
    public static BlockHutSupplyDepot                    SUPPLY_DEPOT_BLOCK;
    public static final Map<WonderType, BlockHutWonder>  WONDER_BLOCKS = new EnumMap<>(WonderType.class);
    public static BlockHutWonder                         WING_BLOCK;

    // ---------------------------------------------------------------- jobs

    public static final ResourceLocation COURIER_ID      = id("tradecourier");
    public static final ResourceLocation QUARTERMASTER_ID = id("quartermaster");

    public static final DeferredHolder<JobEntry, JobEntry> TRADE_COURIER = JOBS.register("tradecourier", () -> new JobEntry.Builder()
        .setJobProducer(JobTradeCourier::new)
        .setJobViewProducer(() -> DefaultJobView::new)
        .setRegistryName(COURIER_ID)
        .createJobEntry());

    public static final DeferredHolder<JobEntry, JobEntry> QUARTERMASTER = JOBS.register("quartermaster", () -> new JobEntry.Builder()
        .setJobProducer(JobQuartermaster::new)
        .setJobViewProducer(() -> DefaultJobView::new)
        .setRegistryName(QUARTERMASTER_ID)
        .createJobEntry());

    // ---------------------------------------------------------------- buildings

    public static final BuildingEntry.ModuleProducer<WorkerBuildingModule, WorkerBuildingModuleView> TRADE_WORK =
        new BuildingEntry.ModuleProducer<>("tradepost_work",
            () -> new WorkerBuildingModule(TRADE_COURIER.get(), Skill.Athletics, Skill.Stamina, true, b -> 1),
            () -> WorkerBuildingModuleView::new);

    public static final BuildingEntry.ModuleProducer<WorkerBuildingModule, WorkerBuildingModuleView> DEPOT_WORK =
        new BuildingEntry.ModuleProducer<>("supplydepot_work",
            () -> new WorkerBuildingModule(QUARTERMASTER.get(), Skill.Knowledge, Skill.Dexterity, true, b -> 1),
            () -> WorkerBuildingModuleView::new);

    public static final DeferredHolder<BuildingEntry, BuildingEntry> TRADE_POST = BUILDINGS.register(BuildingTradePost.SCHEMATIC, () -> new BuildingEntry.Builder()
        .setBuildingBlock(TRADE_POST_BLOCK)
        .setBuildingProducer(BuildingTradePost::new)
        .setBuildingViewProducer(() -> EmptyView::new)
        .setRegistryName(id(BuildingTradePost.SCHEMATIC))
        .addBuildingModuleProducer(TRADE_WORK)
        .createBuildingEntry());

    public static final DeferredHolder<BuildingEntry, BuildingEntry> SUPPLY_DEPOT = BUILDINGS.register(BuildingSupplyDepot.SCHEMATIC, () -> new BuildingEntry.Builder()
        .setBuildingBlock(SUPPLY_DEPOT_BLOCK)
        .setBuildingProducer(BuildingSupplyDepot::new)
        .setBuildingViewProducer(() -> EmptyView::new)
        .setRegistryName(id(BuildingSupplyDepot.SCHEMATIC))
        .addBuildingModuleProducer(DEPOT_WORK)
        .createBuildingEntry());

    public static final Map<WonderType, DeferredHolder<BuildingEntry, BuildingEntry>> WONDERS = new EnumMap<>(WonderType.class);

    static
    {
        for (final WonderType type : WonderType.values())
        {
            WONDERS.put(type, BUILDINGS.register(type.id, () -> new BuildingEntry.Builder()
                .setBuildingBlock(WONDER_BLOCKS.get(type))
                .setBuildingProducer((colony, pos) -> new BuildingWonder(colony, pos, type))
                .setBuildingViewProducer(() -> EmptyView::new)
                .setRegistryName(id(type.id))
                .createBuildingEntry()));
        }
    }

    public static final DeferredHolder<BuildingEntry, BuildingEntry> WONDER_WING = BUILDINGS.register("wonderwing", () -> new BuildingEntry.Builder()
        .setBuildingBlock(WING_BLOCK)
        .setBuildingProducer(BuildingWonder.Wing::new)
        .setBuildingViewProducer(() -> EmptyView::new)
        .setRegistryName(id("wonderwing"))
        .createBuildingEntry());

    public static final DeferredItem<Item> LEDGER = ITEMS.register("trade_ledger", () -> new TradeLedgerItem(new Item.Properties().stacksTo(1)));

    public NeoterraTrade(final IEventBus modBus, final ModContainer container)
    {
        BUILDINGS.register(modBus);
        JOBS.register(modBus);
        ITEMS.register(modBus);
        container.registerConfig(ModConfig.Type.SERVER, NeoterraConfig.SPEC);
        modBus.addListener(this::onRegister);
        modBus.addListener(this::onBlockEntityBlocks);
        modBus.addListener(this::onCreativeTabs);
        NeoForge.EVENT_BUS.register(new ColonyBoosts());
        SelfTest.register();
    }

    public static ResourceLocation id(final String path)
    {
        return ResourceLocation.fromNamespaceAndPath(MOD_ID, path);
    }

    /** All hut blocks of this mod. */
    public static List<AbstractBlockHut<?>> huts()
    {
        final List<AbstractBlockHut<?>> out = new ArrayList<>();
        out.add(TRADE_POST_BLOCK);
        out.add(SUPPLY_DEPOT_BLOCK);
        out.addAll(WONDER_BLOCKS.values());
        out.add(WING_BLOCK);
        return out;
    }

    private void onRegister(final RegisterEvent event)
    {
        event.register(Registries.BLOCK, helper -> {
            TRADE_POST_BLOCK = new BlockHutTradePost();
            SUPPLY_DEPOT_BLOCK = new BlockHutSupplyDepot();
            for (final WonderType type : WonderType.values())
            {
                WONDER_BLOCKS.put(type, new BlockHutWonder(type));
            }
            WING_BLOCK = new BlockHutWonder(null);
            for (final AbstractBlockHut<?> hut : huts())
            {
                helper.register(hut.getRegistryName(), hut);
            }
        });
        event.register(Registries.ITEM, helper -> {
            for (final AbstractBlockHut<?> hut : huts())
            {
                helper.register(hut.getRegistryName(), new ItemBlockHut(hut, new Item.Properties()));
            }
        });
    }

    /** MineColonies' hut block entity only accepts its own hut blocks – add ours to the list. */
    private void onBlockEntityBlocks(final BlockEntityTypeAddBlocksEvent event)
    {
        event.modify(MinecoloniesTileEntities.BUILDING.get(), huts().toArray(new Block[0]));
    }

    private void onCreativeTabs(final BuildCreativeModeTabContentsEvent event)
    {
        if (event.getTabKey() == CreativeModeTabs.FUNCTIONAL_BLOCKS)
        {
            huts().forEach(event::accept);
        }
        if (event.getTabKey() == CreativeModeTabs.TOOLS_AND_UTILITIES)
        {
            event.accept(LEDGER.get());
        }
    }
}
