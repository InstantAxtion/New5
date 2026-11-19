package com.neoterra.trade;

import com.minecolonies.api.client.render.modeltype.ModModelTypes;
import com.minecolonies.api.colony.ICitizenData;
import com.minecolonies.core.colony.jobs.AbstractJob;
import net.minecraft.resources.ResourceLocation;
import org.jetbrains.annotations.NotNull;

/** The Quartermaster of the Supply Depot. */
public class JobQuartermaster extends AbstractJob<EntityAIWorkQuartermaster, JobQuartermaster>
{
    public JobQuartermaster(final ICitizenData entity)
    {
        super(entity);
    }

    @Override
    public EntityAIWorkQuartermaster generateAI()
    {
        return new EntityAIWorkQuartermaster(this);
    }

    @NotNull
    @Override
    public ResourceLocation getModel()
    {
        return ModModelTypes.CRAFTER_ID;
    }
}
