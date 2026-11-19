package com.neoterra.trade;

import com.minecolonies.api.blocks.AbstractBlockHut;
import com.minecolonies.api.colony.buildings.registry.BuildingEntry;
import net.minecraft.resources.ResourceLocation;
import org.jetbrains.annotations.NotNull;

/** The Supply Depot hut block. */
public class BlockHutSupplyDepot extends AbstractBlockHut<BlockHutSupplyDepot>
{
    @NotNull
    @Override
    public String getHutName()
    {
        return "blockhutsupplydepot";
    }

    @Override
    public ResourceLocation getRegistryName()
    {
        return NeoterraTrade.id(getHutName());
    }

    @Override
    public BuildingEntry getBuildingEntry()
    {
        return NeoterraTrade.SUPPLY_DEPOT.get();
    }
}
