package com.neoterra.trade;

import com.minecolonies.api.blocks.AbstractBlockHut;
import com.minecolonies.api.colony.buildings.registry.BuildingEntry;
import net.minecraft.resources.ResourceLocation;
import org.jetbrains.annotations.NotNull;

/** Hut block of a Grand Project (type != null) or of a wonder wing (type == null). */
public class BlockHutWonder extends AbstractBlockHut<BlockHutWonder>
{
    private final WonderType type;

    public BlockHutWonder(final WonderType type)
    {
        super();
        this.type = type;
    }

    @NotNull
    @Override
    public String getHutName()
    {
        return type == null ? "blockhutwonderwing" : "blockhut" + type.id;
    }

    @Override
    public ResourceLocation getRegistryName()
    {
        return NeoterraTrade.id(getHutName());
    }

    @Override
    public BuildingEntry getBuildingEntry()
    {
        return type == null ? NeoterraTrade.WONDER_WING.get() : NeoterraTrade.WONDERS.get(type).get();
    }
}
