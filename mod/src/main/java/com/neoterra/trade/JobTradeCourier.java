package com.neoterra.trade;

import com.minecolonies.api.client.render.modeltype.ModModelTypes;
import com.minecolonies.api.colony.ICitizenData;
import com.minecolonies.core.colony.jobs.AbstractJob;
import net.minecraft.resources.ResourceLocation;
import org.jetbrains.annotations.NotNull;

/** The Trade Courier: carries goods between two linked Trade Posts. */
public class JobTradeCourier extends AbstractJob<EntityAIWorkTradeCourier, JobTradeCourier>
{
    public JobTradeCourier(final ICitizenData entity)
    {
        super(entity);
    }

    @Override
    public EntityAIWorkTradeCourier generateAI()
    {
        return new EntityAIWorkTradeCourier(this);
    }

    @NotNull
    @Override
    public ResourceLocation getModel()
    {
        return ModModelTypes.COURIER_ID;
    }
}
