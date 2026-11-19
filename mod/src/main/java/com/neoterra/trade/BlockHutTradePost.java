package com.neoterra.trade;

import com.minecolonies.api.blocks.AbstractBlockHut;
import com.minecolonies.api.colony.buildings.registry.BuildingEntry;
import net.minecraft.resources.ResourceLocation;
import org.jetbrains.annotations.NotNull;

/** The Trade Post hut block. */
public class BlockHutTradePost extends AbstractBlockHut<BlockHutTradePost>
{
    @NotNull
    @Override
    public String getHutName()
    {
        return "blockhuttradepost";
    }

    @Override
    public ResourceLocation getRegistryName()
    {
        return NeoterraTrade.id(getHutName());
    }

    @Override
    public BuildingEntry getBuildingEntry()
    {
        return NeoterraTrade.TRADE_POST.get();
    }
}
