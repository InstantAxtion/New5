package com.neoterra.trade;

import com.minecolonies.api.entity.ai.JobStatus;
import com.minecolonies.api.entity.ai.statemachine.AITarget;
import com.minecolonies.api.entity.ai.statemachine.states.IAIState;
import com.minecolonies.api.util.EntityUtils;
import com.minecolonies.core.entity.ai.workers.AbstractEntityAIInteract;
import net.minecraft.core.BlockPos;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.Entity;
import org.jetbrains.annotations.NotNull;

import java.util.Optional;

import static com.minecolonies.api.entity.ai.statemachine.states.AIWorkerState.IDLE;
import static com.minecolonies.api.entity.ai.statemachine.states.AIWorkerState.START_WORKING;

/**
 * Trade Courier AI: wait at the post until an order is complete, pack it and set off to the
 * partner colony (the citizen is away for the journey there and back).
 */
public class EntityAIWorkTradeCourier extends AbstractEntityAIInteract<JobTradeCourier, BuildingTradePost>
{
    /** Our own states. */
    enum CourierState implements IAIState
    {
        PACK,
        WAIT;

        @Override
        public boolean isOkayToEat()
        {
            return true;
        }
    }

    public EntityAIWorkTradeCourier(@NotNull final JobTradeCourier job)
    {
        super(job);
        super.registerTargets(
          new AITarget(IDLE, START_WORKING, 20),
          new AITarget(START_WORKING, this::decideWork, 40),
          new AITarget(CourierState.WAIT, this::waitAtPost, 100),
          new AITarget(CourierState.PACK, this::pack, 20)
        );
        worker.setCanPickUpLoot(true);
    }

    @Override
    public Class<BuildingTradePost> getExpectedBuildingClass()
    {
        return BuildingTradePost.class;
    }

    @Override
    public boolean canBeInterrupted()
    {
        return !worker.isInvisible();
    }

    private IAIState decideWork()
    {
        // back from a trip: respawn at the post
        final Optional<BlockPos> target = worker.getCitizenData().getColony().getTravellingManager().getTravellingTargetFor(worker.getCitizenData());
        if (target.isPresent())
        {
            worker.getCitizenData().getColony().getTravellingManager().finishTravellingFor(worker.getCitizenData());
        }
        if (building.getPartner() == null || !building.canExport())
        {
            worker.getCitizenData().setJobStatus(JobStatus.IDLE);
            return CourierState.WAIT;
        }
        if (building.nextReadyOrder() != null)
        {
            return CourierState.PACK;
        }
        return CourierState.WAIT;
    }

    private IAIState waitAtPost()
    {
        if (!walkToBuilding())
        {
            return getState();
        }
        worker.getCitizenData().setVisibleStatus(null);
        return START_WORKING;
    }

    private IAIState pack()
    {
        if (!walkToBuilding())
        {
            return getState();
        }
        final BuildingTradePost.Order order = building.nextReadyOrder();
        if (order == null)
        {
            return START_WORKING;
        }
        final int ticks = building.travelTicks();
        if (!building.dispatch(order, ticks))
        {
            return START_WORKING;
        }
        worker.getCitizenData().setJobStatus(JobStatus.WORKING);
        worker.getCitizenExperienceHandler().addExperience(1.0);
        worker.playSound(SoundEvents.HORSE_SADDLE, 0.6F, 1.0F);
        // out to the partner and back again
        worker.getCitizenData().setNextRespawnPosition(EntityUtils.getSpawnPoint(building.getColony().getWorld(), building.getPosition()));
        worker.getCitizenData().getColony().getTravellingManager().startTravellingTo(worker.getCitizenData(), building.getPosition(), ticks * 2);
        worker.remove(Entity.RemovalReason.DISCARDED);
        return IDLE;
    }
}
